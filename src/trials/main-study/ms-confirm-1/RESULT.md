# Confirmatory test 1: result

Failed. The primary rule caught every cartel but flagged 5/24 innocent games. The secondary price + overreaction rule flagged 16/16 against 0/24, so confirmatory test 2 made it primary and retested it on fresh seeds.

| Rule | P+W | B+C+D | One-sided Fisher p |
|---|---|---|---|
| Price + punish (primary) | 16/16 | 5/24 | 3.2e-07 |
| Price + overreaction (secondary) | 16/16 | 0/24 | 1.6e-11 |

Per arm, price + overreaction: P 8/8, W 8/8, B 0/8, C 0/8, D 0/8, A 0/8. Data: `run/` (`summary.md` holds every detector and the test-set cases).
