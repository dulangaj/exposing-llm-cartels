# Blocks until the Modal vLLM server answers a chat call, so a cold start can't turn early rounds into fallbacks.
import os, sys, time, json, urllib.request
url, key = os.environ["MODAL_LLM_URL"].rstrip("/") + "/v1/chat/completions", os.environ["MODAL_LLM_TOKEN"]
body = json.dumps({"model": os.environ.get("CS_SERVED", "qwen3-8b"), "messages": [{"role": "user", "content": "Say ok."}], "max_tokens": 8,
                   "chat_template_kwargs": {"enable_thinking": False}}).encode()
start = time.time()
while time.time() - start < 1500:
    try:
        req = urllib.request.Request(url, body, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=120).read()
        sys.exit(print(f"server warm after {time.time() - start:.0f}s"))
    except Exception as e:
        print(f"warming ({time.time() - start:.0f}s): {type(e).__name__}", flush=True)
        time.sleep(15)
sys.exit("server never answered")
