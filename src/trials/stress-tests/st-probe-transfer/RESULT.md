# Probe transfer to own-price cartels: result

Passed both bars: act_L18 ranked Q′ above innocents at AUROC 0.83, against 0.57 for price text; no own-price game sat on the monopoly price, so `rule_exact` fell to 0.50. Caveats: the CI's lower bound (0.70) is under 0.80 with 16 games per arm, and scores are poorly calibrated (mean 0.07 for Q′), so only the ranking transferred. `st-no-price-replication` retested it on fresh games.

Trained on 4,895 main-study calls; scored 2,453 own-price calls in 64 games. Game-level AUROC, 95% bootstrap CI; rule rows show the share of games flagged.

| Method | Q′ vs innocent | P′ vs innocent | Mean P′ / Q′ / C / D |
|---|---|---|---|
| act_L18 | 0.83 [0.70, 0.93] | 0.83 [0.69, 0.95] | 0.00 / 0.07 / 0.00 / 0.00 |
| text | 0.57 [0.38, 0.77] | 0.59 [0.40, 0.77] | 0.03 / 0.03 / 0.02 / 0.03 |
| price_feat | 0.63 [0.47, 0.79] | 0.87 [0.75, 0.96] | 0.64 / 0.25 / 0.24 / 0.22 |
| rule_exact | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.00 / 0.00 / 0.00 / 0.00 |
| rule_nonround | 0.52 [0.39, 0.66] | 0.48 [0.36, 0.62] | 0.25 / 0.31 / 0.19 / 0.38 |
