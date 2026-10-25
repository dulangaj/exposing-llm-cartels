"""Minimal chat client for our Modal-hosted vLLM server, with a shared cost and deadline cap."""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Running USD total shared by every run in a process; trips once it passes the cap or the deadline
    (a time.time() value). Spend also counts toward the parent budget, whose trip stops this one too."""

    def __init__(self, cap, deadline=None, parent=None):
        self.cap, self.deadline, self.parent, self.spent, self.calls = cap, deadline, parent, 0.0, 0
        self._lock = threading.Lock()

    def check(self):
        if self.parent:
            self.parent.check()
        if self.deadline is not None and time.time() > self.deadline:
            raise BudgetExceeded("deadline")
        if self.spent > self.cap:
            raise BudgetExceeded(f"spent ${self.spent:.4f} > cap ${self.cap:.2f}")

    def add(self, cost):
        with self._lock:
            self.spent += cost or 0.0
            self.calls += 1
        if self.parent:
            self.parent.add(cost)
        self.check()


def post(req, timeout, attempts=5):
    """urlopen + JSON decode; retries 429/5xx with backoff (retry-after when given), raises other errors."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500 or attempt == attempts - 1:
                raise
            time.sleep(float(e.headers.get("retry-after") or 2 ** attempt))


class OpenAICompat:
    """OpenAI-compatible chat completions on our Modal vLLM server (modal_app/vllm_server.py) at MODAL_LLM_URL,
    authenticated with the vLLM API key MODAL_LLM_TOKEN. Cost is 0 per call: Modal bills GPU time.
    thinking=True turns on Qwen3's reasoning; it is stripped from the reply and its length kept in usage.
    max_think_tokens caps the reasoning: a reply cut off mid-thought is closed and continued for an answer
    (Qwen3's budget forcing), so a capped call still returns a price."""
    THINK = re.compile(r"<think>(.*?)(?:</think>\s*|$)", re.S)  # an unclosed block was cut off by max_tokens
    # Qwen3's thinking-budget sentence; vLLM's continue_final_message then completes the assistant turn.
    FORCE = ("\n\nConsidering the limited time by the user, I have to give the solution based on the thinking "
             "directly now.\n</think>")
    ANSWER_TOKENS = 512

    def __init__(self, model, budget, timeout=180, thinking=False, max_think_tokens=None):
        self.url, self.key = os.environ.get("MODAL_LLM_URL"), os.environ.get("MODAL_LLM_TOKEN")
        if not self.url or not self.key:
            raise SystemExit("MODAL_LLM_URL and MODAL_LLM_TOKEN must be set")
        self.url = self.url.rstrip("/") + "/v1/chat/completions"
        self.model, self.budget, self.timeout, self.thinking = model, budget, timeout, thinking
        self.max_think_tokens = max_think_tokens

    def _post(self, body):
        self.budget.check()
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers={
            "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        data = post(req, self.timeout)
        self.budget.add(0.0)
        return data["choices"][0]["message"]["content"] or "", data.get("usage") or {}

    def chat(self, messages):
        """Returns (text, usage): prompt/completion tokens, cost, provider and reasoning_chars. Retries 429/5xx with backoff."""
        # Qwen3 thinks by default; the chat-template switch turns it off unless asked, so replies stay short.
        cap = (self.max_think_tokens or 4096) if self.thinking else 2048
        body = {"model": self.model, "messages": messages, "max_tokens": cap,
                "chat_template_kwargs": {"enable_thinking": self.thinking}}
        text, u = self._post(body)
        prompt, completion = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
        if self.thinking and self.max_think_tokens and "<think>" in text and "</think>" not in text:
            prefix = "<think>\n" + text.split("<think>", 1)[1].strip() + self.FORCE
            try:
                rest, u = self._post({**body, "max_tokens": self.ANSWER_TOKENS, "add_generation_prompt": False,
                                      "continue_final_message": True,
                                      "messages": messages + [{"role": "assistant", "content": prefix}]})
                text, completion = prefix + rest, completion + u.get("completion_tokens", 0)
            except urllib.error.HTTPError as e:  # a server that rejects continuation: the reply stays empty
                if e.code >= 500 or e.code == 429:
                    raise
        usage = {"prompt_tokens": prompt, "completion_tokens": completion, "cost": 0.0, "provider": "modal",
                 "reasoning_chars": sum(len(m.group(1).strip()) for m in self.THINK.finditer(text))}
        return self.THINK.sub("", text), usage


def client(model, budget, timeout=180, thinking=False, max_think_tokens=None):
    """modal:<served name> -> our Modal vLLM server; any other id raises ValueError."""
    if not model.startswith("modal:"):
        raise ValueError(f"unsupported model {model!r}: only modal:<name> is supported")
    return OpenAICompat(model.removeprefix("modal:"), budget, timeout, thinking, max_think_tokens)
