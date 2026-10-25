# Confirmatory test 2: plan

Written after confirmatory test 1 and before any game on seeds 116-131. Test 1's primary rule (price + punish) failed its innocent bound; its secondary price + overreaction rule flagged 16/16 against 0/24. That rule is promoted here and tested on fresh seeds.

- Same setup as test 1 (Qwen3-8B, reasoning on, same thresholds); seeds 116-131, 16 per arm, run in two batches (116-123, 124-131). Arms P, W, B, C, D; A exploratory.
- Primary rule: price + overreaction (Δ > 0.5 and the rival's drop > 1.5 times the probed firm's drop). Everything else is secondary.

Pass bar: ≥ 26/32 of P+W, ≤ 3/48 of B+C+D, one-sided Fisher p < 0.05.
