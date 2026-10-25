# No stated price, replication (activation probe): result

Not confirmed: at the fixed threshold the probe flagged 5/32 Q′ games against 6/64 innocent games (one-sided Fisher p = 0.28). Innocent flags rose from 1/32 to 6/64, so the threshold did not hold. AUROC fell to 0.71, under the 0.80 bar, and one shuffled-label refit reached 0.79 (permutation p = 0.095). P′, whose prompt still states a rule, did separate (15/32, p = 6.1e-05), but Δ + overreaction ranked P′ better (0.83). `st-probe-transfer` is therefore exploratory.

4,891 calls in 128 games, scored by the fixed models at the fixed thresholds. Flags with 95% Wilson CI; one-sided Fisher against C+D; game-level AUROC with 95% bootstrap CI.

| Method | Q′ flagged | P′ flagged | C+D flagged | Fisher p (Q′) | Fisher p (P′) | AUROC Q′ vs innocent | AUROC P′ vs innocent |
|---|---|---|---|---|---|---|---|
| act_L18 | 5/32 [0.07, 0.32] | 15/32 [0.31, 0.64] | 6/64 [0.04, 0.19] | 0.28 | 6.1e-05 | 0.71 [0.60, 0.81] | 0.79 [0.68, 0.89] |
| text | 4/32 [0.05, 0.28] | 2/32 [0.02, 0.20] | 3/64 [0.02, 0.13] | 0.16 | 0.54 | 0.50 [0.37, 0.63] | 0.61 [0.48, 0.73] |
| price_feat | 3/32 [0.03, 0.24] | 2/32 [0.02, 0.20] | 1/64 [0.00, 0.08] | 0.11 | 0.26 | 0.66 [0.55, 0.77] | 0.83 [0.74, 0.91] |

- Primary (act_L18 at threshold 0.003428): not confirmed (p = 0.28).
- AUROC ≥ 0.80: no; activation win (≥ TF-IDF + 0.15): yes.
- Shuffled-label refits: Q′ AUROC median 0.49, max 0.79; permutation p = 0.095.
- Exploratory, main-study arm A: 3/24 games above the act_L18 threshold.
