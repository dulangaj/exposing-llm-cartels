"""Pooled Qwen3-8B residuals over each replayed firm call's own output tokens, on one Modal H100.

modal run trials/stress-tests/st-activation-probe/acts_modal.py --out trials/stress-tests/st-activation-probe/acts [--runs dir,dir] [--limit N] [--hosts]

The local entrypoint needs only the standard library and modal: it builds the replay (replay.py), downloads the
weights on a CPU container into the shared huggingface-cache Volume, then streams chunks to one H100 and writes
replay.jsonl plus, per chunk k and layer L, part{k:03d}_L{L}.npy (float16, rows in replay order).
"""
import json
import sys
from pathlib import Path

import modal

MODEL = "Qwen/Qwen3-8B"
LAYERS = (12, 18, 24)
CHUNK = 32  # calls per remote call; keeps each result under Modal's 2 MiB inline limit (no blob-store host)
BATCH_TOKENS = 24_000  # padded tokens per forward pass
MINUTES = 60

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.8.0", "transformers==4.57.1", "numpy", "huggingface_hub[hf_xet]")
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)
hf_cache = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
app = modal.App("cs-activation-probe")
VOLUMES = {"/root/.cache/huggingface": hf_cache}


@app.function(image=image, volumes=VOLUMES, timeout=20 * MINUTES)
def download():
    from huggingface_hub import snapshot_download

    snapshot_download(MODEL, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"])
    hf_cache.commit()


@app.cls(image=image, gpu="H100", volumes=VOLUMES, max_containers=1, timeout=30 * MINUTES, scaledown_window=60)
class Acts:
    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, attn_implementation="sdpa")
        self.model.to("cuda").eval()

    def encode(self, row):
        """Token ids of the replayed chat and the index where the firm's own output starts."""
        prefix = self.tok.apply_chat_template([{"role": "system", "content": row["system"]},
                                               {"role": "user", "content": row["user"]}],
                                              tokenize=False, add_generation_prompt=True, enable_thinking=False)
        pre = self.tok(prefix, add_special_tokens=False)["input_ids"]
        out = self.tok(row["output"], add_special_tokens=False)["input_ids"]
        return pre + out, len(pre)

    @modal.method()
    def pooled(self, rows):
        import io

        import numpy as np
        import torch

        enc = [self.encode(r) for r in rows]
        order = sorted(range(len(enc)), key=lambda i: len(enc[i][0]))
        res = {L: np.zeros((len(rows), self.model.config.hidden_size), np.float32) for L in LAYERS}
        batches, cur = [], []
        for i in order:
            if cur and len(enc[i][0]) * (len(cur) + 1) > BATCH_TOKENS:
                batches.append(cur)
                cur = []
            cur.append(i)
        batches.append(cur)
        for b in batches:
            n = max(len(enc[i][0]) for i in b)
            ids = torch.full((len(b), n), self.tok.pad_token_id, dtype=torch.long)
            attn, mask = torch.zeros((len(b), n), dtype=torch.long), torch.zeros((len(b), n))
            for j, i in enumerate(b):
                toks, start = enc[i]
                ids[j, :len(toks)], attn[j, :len(toks)], mask[j, start:len(toks)] = torch.tensor(toks), 1, 1
            with torch.no_grad():  # the base model skips the 152k-vocab logits
                hs = self.model.model(input_ids=ids.cuda(), attention_mask=attn.cuda(), output_hidden_states=True,
                                use_cache=False).hidden_states
            m = mask.cuda()[..., None]
            for L in LAYERS:
                pooled = (hs[L].float() * m).sum(1) / m.sum(1)
                res[L][b] = pooled.cpu().numpy()
        out = {}
        for L in LAYERS:
            buf = io.BytesIO()
            np.save(buf, res[L].astype(np.float16))
            out[L] = buf.getvalue()
        return out


@app.local_entrypoint()
def main(out: str = "trials/stress-tests/st-activation-probe/acts", runs: str = "", limit: int = 0, hosts: bool = False):
    if hosts:  # which input-plane host function calls need (the Tart guest reaches only allowlisted hosts)
        from modal._utils.async_utils import synchronizer

        f = synchronizer._translate_in(download.hydrate())
        print("input_plane_url:", f._input_plane_url, f._input_plane_region, flush=True)
        return
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import replay

    rows = replay.build(runs.split(",") if runs else replay.RUNS)[:limit or None]
    d = Path(out)
    d.mkdir(parents=True, exist_ok=True)
    (d / "replay.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} calls; downloading {MODEL}", flush=True)
    download.remote()
    chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
    for k, res in enumerate(Acts().pooled.map(chunks)):  # map keeps input order
        for L, blob in res.items():
            (d / f"part{k:03d}_L{L}.npy").write_bytes(blob)
        print(f"chunk {k + 1}/{len(chunks)}", flush=True)
