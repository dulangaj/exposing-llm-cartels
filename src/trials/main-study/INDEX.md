# Main study

Each confirmatory stage folder holds `PLAN.md` (written before its runs) and `RESULT.md`. The exploratory pilot has no plan; its results are `runs-modal/fit.md`, `runs-modal/test/summary.md` and `runs-modal-thinking/combined/summary.md`. `ms-analysis/` holds reports only.

In the pilot, arm X is a silent innocent whose firm 1 may use another model (`--x-model`; here also Qwen3-8B), so it counts among the 16 innocent test games in paper Appendix B. Test seeds 104-105 (`runs-modal/test-a/`) and 106-107 (`test-b/`) ran in two batches; `test/` scores them together.

| Path | What | Outcome |
|---|---|---|
| `ms-pilot-phase/` | Exploratory pilot, seeds 100-107 (paper Appendix B) | Picked the punish threshold; reasoning-off cartels did not punish |
| `ms-confirm-1/` | Confirmatory test 1, seeds 108-115 | Primary price + punish failed (5/24 innocents); price + overreaction 16/16 vs 0/24 |
| `ms-confirm-2/` | Confirmatory test 2, seeds 116-131, price + overreaction primary | Passed, 32/32 vs 0/48 |
| `ms-qwen14b/` | Replication on Qwen3-14B | Passed, 14/16 vs 0/24 |
| `ms-agree-only/` | Cartels with no punishment rule (Q) | 0/16 |
| `ms-analysis/` | Per-arm flag rates, placebos and threshold sweeps per stage (`python3 -m sprint.seed_analysis`) | |
| `primary.py` | Primary readout: flags per arm and one-sided Fisher test | |
| `variance.py` | Per-game over-reaction spread (paper §4.1) | |
| `figure.py` | Paper Figure 2 (`paper/fig_flags.svg`) | |
| `warmup.py` | Waits for the model server before the first game | |
