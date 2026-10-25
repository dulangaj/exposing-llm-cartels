# Harness

Two LLM firms (Qwen3-8B or Qwen3-14B on vLLM, one Modal H100) set prices in a repeated logit duopoly; detectors are scored on labelled cartel and innocent games. Thresholds for every stage are `TH` in `sprint/plusfactor.py` (Δ 0.5, punish 0.1, overreaction 1.5, judge 0.5).

| Path | What |
|---|---|
| `sprint/` | Market, agents, LLM client, detectors, statistics |
| `modal_app/` | vLLM server for Modal (see its README) |
| `tests/` | Offline unit tests (mock agents, no network) |
| `trials/main-study/` | Main study (`ms-*`, see `INDEX.md`) |
| `trials/stress-tests/` | Stress tests (`st-*`, see `INDEX.md`) |

## Reproduce

Run from this folder. The first block is offline and takes about a minute.

```sh
python3 -m unittest    # 76 tests, OK with 7 skipped without numpy/scikit-learn
MS=trials/main-study; ST=trials/stress-tests
python3 $MS/primary.py $MS/ms-confirm-2/run-116-123 $MS/ms-confirm-2/run-124-131             # 32/32 vs 0/48
python3 $MS/primary.py $MS/ms-qwen14b/run                                                     # 14/16 vs 0/24
python3 $MS/primary.py $MS/ms-confirm-1/run                                                   # 16/16 vs 0/24
python3 $MS/primary.py $MS/ms-agree-only/run --pos Q --neg D                                  # Q 0/16 vs D 0/16
python3 $MS/primary.py $ST/st-followup-runs-8b/reasoning-off --pos P --neg C,D                # reasoning off 0/16
python3 $MS/primary.py $ST/st-no-price-replication/games --pos P --neg C,D                    # no stated price 0/32
python3 $MS/variance.py                                                                       # per-game spread, paper §4.1 and Appendix D
```

The activation-probe scripts (`st-activation-probe/`, `st-probe-transfer/`, `st-no-price-replication/analyze.py`) need numpy and scikit-learn and the activation arrays, which are not included; `acts_modal.py` extracts them.

Live rerun (Qwen3-8B, reasoning on, 4 games; the command caps play at 15 minutes and judging at 4, plus server start-up). Set up Modal as in `modal_app/README.md` (Python >= 3.10; macOS ships 3.9, so install one, e.g. with `uv python install 3.12`); `warmup.py` waits until the server answers (it prints HTTP errors for the 2 to 4 minutes the server takes to start). Results go to `live/`.

```sh
export MODAL_LLM_TOKEN=$(openssl rand -hex 24)                          # once
modal secret create cs-eval-llm-key VLLM_API_KEY="$MODAL_LLM_TOKEN"     # once
find . -exec touch {} +    # resets unzipped file times, or modal deploy can refuse with "modified during build"
modal deploy modal_app/vllm_server.py
export MODAL_LLM_URL=<printed URL>
python3 trials/main-study/warmup.py
# --x-model: firm 1's model in the cross-model arm X (not run here); --wall: seconds before firm play stops;
# --judge-wall: seconds the judge then gets; --budget / --judge-budget: USD caps on firm and judge calls
python3 -m sprint.testset_run --phase test --seeds 900-901 --scenarios P,D --out live --rounds 20 --firm-model modal:qwen3-8b --x-model modal:qwen3-8b --judge-model modal:qwen3-8b --thinking --wall 900 --judge-wall 240 --budget 3 --judge-budget 1
modal app stop -y cs-eval-llm
```

Stress-test runs: `bash trials/stress-tests/batch.sh` (screens) and `bash trials/stress-tests/xbatch.sh 8b|14b|no-price-replication <out dir>` (follow-ups).
