# Activation probe: result

Not passed, because a baseline was already perfect: activations and price-only TF-IDF both separated cartel from innocent games at AUROC 1.00, Q included. Cartels held the exact monopoly price their prompt stated ($1.92, $6.16 or $19.25 by price scale), innocents round numbers, and TF-IDF's top features were those price strings. Δ and overreaction were near chance on Q (0.45), so the gap is the price level, not the dynamics the price-cut probe reads.

4,895 calls, 128 games; game-level AUROC, 8 leave-game-out folds, 95% bootstrap CI.

| Features | Cartel vs innocent | Q vs innocent | Q vs C | Q vs D | Transfer Q vs innocent | Mean score P / Q / C / D / A |
|---|---|---|---|---|---|---|
| act_L12 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 1.00 / 1.00 / 0.00 / 0.00 / 0.00 |
| act_L18 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 1.00 / 1.00 / 0.01 / 0.00 / 0.00 |
| act_L24 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 1.00 / 1.00 / 0.00 / 0.00 / 0.00 |
| text | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 0.96 / 0.96 / 0.03 / 0.03 / 0.04 |
| price_feat | 0.78 [0.67, 0.87] | 0.45 [0.32, 0.56] | 0.50 | 0.41 | 0.50 [0.38, 0.61] | 0.87 / 0.21 / 0.23 / 0.28 / 0.19 |

Activations are not included; `analyze.py` reproduces this table from them.
