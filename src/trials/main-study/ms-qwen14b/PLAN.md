# Qwen3-14B replication: plan

Does the probe carry over to a larger model without retuning?

- Qwen3-14B-FP8 firms and judge, reasoning on; same thresholds, 20 rounds, probe depth 0.5.
- Seeds 116-123, arms P, W, B, C, D (8 each); A exploratory.
- Rule: price + overreaction. A failure is reported as a failure to transfer, not retuned.

Pass bar: ≥ 12/16 of P+W, ≤ 2/24 of B+C+D, one-sided Fisher p < 0.05.
