"""OpenAI-compatible vLLM server for one open-weight model on a single Modal H100.

Follows Modal's vLLM example (https://modal.com/docs/examples/vllm_inference) and Servers guide
(https://modal.com/docs/guide/servers). vLLM's --api-key, read from the Modal Secret cs-eval-llm-key (VLLM_API_KEY), rejects
requests without the matching bearer token. Deploy (optionally CS_MODEL=... CS_SERVED=...): modal deploy modal_app/vllm_server.py
"""
import os
import subprocess

import modal

MODEL = os.environ.get("CS_MODEL", "Qwen/Qwen3-8B-FP8")  # read at deploy time and passed to the container below
SERVED_NAME = os.environ.get("CS_SERVED", "qwen3-8b")  # client model id: modal:<CS_SERVED>
MINUTES = 60

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.21.0")
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "CS_MODEL": MODEL, "CS_SERVED": SERVED_NAME})
)
hf_cache = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache", create_if_missing=True)
app = modal.App("cs-eval-llm")


@app.server(
    image=image,
    gpu="H100",
    secrets=[modal.Secret.from_name("cs-eval-llm-key")],
    unauthenticated=True,  # skip Modal's proxy auth; vLLM's --api-key checks the bearer token
    volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
    max_containers=1,
    scaledown_window=5 * MINUTES,  # idle containers stop after 5 min
    startup_timeout=15 * MINUTES,  # first boot downloads the weights
    target_concurrency=64,
    max_concurrency=128,  # vLLM queues beyond its KV budget; 429s past this are retried by the client
)
class Server:
    @modal.enter()
    def start(self):
        self.process = subprocess.Popen([
            "vllm", "serve", MODEL, "--served-model-name", SERVED_NAME,
            "--host", "0.0.0.0", "--port", "8000",
            "--max-model-len", "16384", "--max-num-seqs", "128", "--gpu-memory-utilization", "0.92",
            "--api-key", os.environ["VLLM_API_KEY"],
        ])

    @modal.exit()
    def stop(self):
        self.process.terminate()
