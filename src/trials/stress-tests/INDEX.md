# Stress tests

Six variables were drawn at random (`st-variable-draw/`). Four ran as 8-seed screens against a rerun of the main setup; two rescored main-study logs. Flagged screens led to three follow-ups. Each test folder holds `PLAN.md` (written before its runs) and `RESULT.md`.

| Folder | What changed | Outcome |
|---|---|---|
| `st-baseline/` | Nothing (rerun of the main setup, seeds 300-307) | P 8/8, Q 0/8, C 0/8; the stated price leaks into prices |
| `st-paraphrase/` | Every message reworded | No change |
| `st-history-order/` | Oldest-first history; one-round message delay | No change |
| `st-short-history/` | 3-round history; no private plan | No change |
| `st-reasoning-off/` | Reasoning off | P 0/8 |
| `st-reasoning-off-followup/` | Reasoning off: 16 seeds, deeper or second cut, Qwen3-14B | P 0/16, not recovered; Qwen3-14B 3/8 |
| `st-no-price/` | No price in the cartel prompt (P′, Q′) | P′ 2/16; the price fingerprint vanishes |
| `st-no-price-replication/` | Same, 128 fresh games; activation probe retest | P′ 0/32; price + punish 19/32 vs 6/64; probe not confirmed |
| `st-judge-swap/` | Gemma 3 27B judge; probe-window view; antitrust standard | Innocent flags 68/72, 72/72, 31/72 |
| `st-activation-probe/` | Activation probe on a price-only replay | AUROC 1.00, matched by price text |
| `st-probe-transfer/` | Same probe on the `st-no-price` games | Q′ AUROC 0.83 vs 0.57 for price text (exploratory) |

Game data: `st-screen-runs/` (screens), `st-followup-runs-8b/` and `st-followup-runs-14b/` (follow-ups), `st-no-price-replication/games/`, `st-probe-transfer/games/`.

Scripts: `batch.sh` runs the screens and `xbatch.sh 8b|14b|no-price-replication <out dir>` the follow-ups; `screen.py` and `xread.py` read the results.
