# Activation probe: plans give the cartel away

Exploratory check on the first replay design (history with plans and messages, reply with price and plan), run before any activation was taken. The firms' own plans name the agreement (Q: "uphold collusive agreement"), so TF-IDF on the words alone separated every arm perfectly and no probe could beat it by 0.15. The replay was therefore made price-only.

| TF-IDF + logistic regression, 8 leave-game-out folds | Cartel vs innocent | Q vs innocent | Q vs C | Q vs D | P→Q transfer | Mean score P / Q / C / D / A |
|---|---|---|---|---|---|---|
| user prompt + output | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 0.97 / 0.96 / 0.03 / 0.02 / 0.05 |
| output only | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 0.96 / 0.94 / 0.04 / 0.03 / 0.06 |
