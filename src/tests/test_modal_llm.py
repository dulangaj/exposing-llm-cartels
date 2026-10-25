import contextlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from sprint import llm
from sprint import testset_run as ts
from tests.test_fail_fast import Resp

ENV = {"MODAL_LLM_URL": "https://ws--cs-eval-llm-server.modal.run/", "MODAL_LLM_TOKEN": "test-key"}
OK = {"choices": [{"message": {"content": "<think>\n\n</think>\n\nPRICE: 1.7"}}],
      "usage": {"prompt_tokens": 12, "completion_tokens": 5}}


class OpenAICompatTest(unittest.TestCase):
    def chat(self, replies, budget=None, thinking=False):
        """replies: dicts (200 JSON bodies) or ints (HTTP error codes), served in order."""
        seen, replies = [], list(replies)

        def opener(req, timeout=0):
            seen.append(req)
            r = replies.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "err", {"retry-after": "0"}, None)
            return Resp(json.dumps(r).encode())

        budget = budget or llm.Budget(1)
        with mock.patch.dict(os.environ, ENV), mock.patch.object(llm.urllib.request, "urlopen", opener), \
                mock.patch.object(llm.time, "sleep"):
            out = llm.client("modal:qwen3-8b", budget, thinking=thinking).chat([{"role": "user", "content": "hi"}])
        return out, seen

    def test_routing(self):
        with mock.patch.dict(os.environ, ENV):
            self.assertIsInstance(llm.client("modal:qwen3-8b", llm.Budget(1)), llm.OpenAICompat)
            for model in ("claude-haiku-5-5", "qwen/qwen3-8b"):
                with self.assertRaises(ValueError):
                    llm.client(model, llm.Budget(1))

    def test_missing_env_exits(self):
        with mock.patch.dict(os.environ, {"MODAL_LLM_URL": ""}), self.assertRaises(SystemExit):
            llm.client("modal:qwen3-8b", llm.Budget(1))

    def test_request_and_response(self):
        budget = llm.Budget(1)
        (text, usage), [req] = self.chat([OK], budget)
        self.assertEqual(req.full_url, "https://ws--cs-eval-llm-server.modal.run/v1/chat/completions")
        self.assertEqual(req.get_header("Authorization"), "Bearer test-key")
        body = json.loads(req.data)
        self.assertEqual(body["model"], "qwen3-8b")
        self.assertEqual(body["messages"], [{"role": "user", "content": "hi"}])
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(text, "PRICE: 1.7")
        self.assertEqual(usage, {"prompt_tokens": 12, "completion_tokens": 5, "cost": 0.0, "provider": "modal",
                                 "reasoning_chars": 0})
        self.assertEqual((budget.spent, budget.calls), (0.0, 1))

    def test_thinking_strips_reasoning_and_counts_it(self):
        reply = {"choices": [{"message": {"content": "<think>\nundercut? no\n</think>\n\n{\"price\": 1.9}"}}]}
        (text, usage), [req] = self.chat([reply], thinking=True)
        body = json.loads(req.data)
        self.assertEqual((body["chat_template_kwargs"], body["max_tokens"]), ({"enable_thinking": True}, 4096))
        self.assertEqual((text, usage["reasoning_chars"]), ('{"price": 1.9}', len("undercut? no")))
        cut = {"choices": [{"message": {"content": "<think>\nstill thinking {\"price\": 1.0}"}}]}
        (text, usage), _ = self.chat([cut], thinking=True)  # cut off by max_tokens: no price leaks out
        self.assertEqual(text, "")
        self.assertGreater(usage["reasoning_chars"], 0)

    def chat_capped(self, replies, cap=256):
        seen, replies = [], list(replies)

        def opener(req, timeout=0):
            seen.append(json.loads(req.data))
            r = replies.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "err", {}, None)
            return Resp(json.dumps(r).encode())

        with mock.patch.dict(os.environ, ENV), mock.patch.object(llm.urllib.request, "urlopen", opener):
            c = llm.client("modal:qwen3-8b", llm.Budget(1), thinking=True, max_think_tokens=cap)
            return c.chat([{"role": "user", "content": "hi"}]), seen

    def test_max_think_tokens_caps_reasoning_and_forces_an_answer(self):
        cut = {"choices": [{"message": {"content": "<think>\nmaybe hold "}}], "usage": {"completion_tokens": 256}}
        answer = {"choices": [{"message": {"content": '\n\n{"price": 1.8}'}}], "usage": {"completion_tokens": 9}}
        (text, usage), [first, second] = self.chat_capped([cut, answer])
        self.assertEqual(first["max_tokens"], 256)
        self.assertNotIn("continue_final_message", first)
        self.assertEqual((second["continue_final_message"], second["add_generation_prompt"]), (True, False))
        self.assertEqual(second["max_tokens"], llm.OpenAICompat.ANSWER_TOKENS)
        prefix = second["messages"][-1]
        self.assertEqual(prefix["role"], "assistant")
        self.assertTrue(prefix["content"].startswith("<think>\nmaybe hold") and prefix["content"].endswith("</think>"))
        self.assertEqual((text, usage["completion_tokens"]), ('{"price": 1.8}', 265))
        done = {"choices": [{"message": {"content": "<think>ok</think>{\"price\": 2}"}}]}
        (text, _), seen = self.chat_capped([done])  # finished within the cap: one call
        self.assertEqual((text, len(seen)), ('{"price": 2}', 1))
        (text, _), seen = self.chat_capped([cut, 400])  # continuation rejected: empty reply, firm falls back
        self.assertEqual((text, len(seen)), ("", 2))

    def test_retries_429_and_5xx(self):
        (text, _), seen = self.chat([429, 503, OK])
        self.assertEqual((text, len(seen)), ("PRICE: 1.7", 3))

    def test_4xx_raises_without_retry(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.chat([401, OK])


class ModelFlagsTest(unittest.TestCase):
    def test_summary_records_models(self):
        out = tempfile.mkdtemp()
        with contextlib.redirect_stdout(io.StringIO()):
            ts.main(["--mock", "--phase", "test", "--seeds", "104", "--rounds", "14", "--out", out,
                     "--firm-model", "modal:qwen3-8b", "--x-model", "modal:qwen3-14b", "--judge-model", "modal:qwen3-8b"])
        with open(os.path.join(out, "summary.json")) as f:
            summary = json.load(f)
        self.assertEqual((summary["model"], summary["rival_model"], summary["judge_model"]),
                         ("modal:qwen3-8b", "modal:qwen3-14b", "modal:qwen3-8b"))
