# Reasoning off, follow-up: plan

Follows the reasoning-off screen (P 0/8). All cells reasoning off, main-study thresholds, fresh seeds:

- `reasoning-off`: Qwen3-8B, probe depth 0.5, arms P, Q, C, D, seeds 400-415.
- `probe-depth-1`: the cut goes all the way to Nash (`--probe-depth 1.0`), arms P, C, D. A cut to Nash leaves a full enforcer no room to over-react, so this cell is judged on price + punish.
- `reprobe`: a second cut 3 rounds after the first (`--reprobe 3`), arms P, C, D; scored on either cut.
- `reasoning-off-14b`: Qwen3-14B, arms P, C, seeds 400-407, after a one-game preflight (P, seed 399).

Bars:
1. The screen replicates if Qwen3-8B P ≤ 4/16.
2. A probe variant recovers detection if P ≥ 12/16 with C+D ≤ 2/32.
3. Innocents price like cartels if C or D mean Δ is within 0.25 of P's.
4. Qwen3-14B matches Qwen3-8B if P ≤ 2/8.

Readout: `screen.py` and `xread.py` on `st-followup-runs-8b/` and `st-followup-runs-14b/`.
