# Screen baseline: plan

A rerun of the main-study setup (Qwen3-8B, reasoning on, 20 rounds, probe depth 0.5, main-study thresholds) with arms P, Q and C on fresh seeds 300-307. The four screens (`st-paraphrase`, `st-history-order`, `st-reasoning-off`, `st-short-history`) use the same seeds and are each compared with it.

Screen bar: a screen is flagged for follow-up if P recall falls below 6/8, Q or C reach 2/8 flags, or any arm's mean Δ moves by 0.25 or more. Eight seeds catch only large effects, so a flag earns a follow-up, not a conclusion.

Readout: `python3 trials/stress-tests/screen.py trials/stress-tests/st-screen-runs baseline <screen cells>`.
