# Modal LLM server

`vllm_server.py` serves `Qwen/Qwen3-8B-FP8` as `qwen3-8b` behind an OpenAI-compatible API on one H100, for `modal:qwen3-8b` in `sprint/llm.py`. Deploy with `CS_MODEL=Qwen/Qwen3-14B-FP8 CS_SERVED=qwen3-14b` to serve another model (the judge-swap test served Gemma 3 27B this way).

```sh
pip install modal && modal setup                 # once; needs Python >= 3.10
export MODAL_LLM_TOKEN=$(openssl rand -hex 24)   # once
modal secret create cs-eval-llm-key VLLM_API_KEY="$MODAL_LLM_TOKEN"   # once; the key vLLM checks
modal deploy modal_app/vllm_server.py            # prints the server URL
export MODAL_LLM_URL=<the printed https://...modal.direct URL>
modal app stop cs-eval-llm                       # when done
```
