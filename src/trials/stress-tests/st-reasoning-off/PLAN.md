# Reasoning off: plan

Does the probe need the firm to reason? Firms run with Qwen3 reasoning off (up to 2,048 output tokens per call), arms P, Q, C, otherwise as `st-baseline`. A one-game preflight (P, seed 299) must finish with no fallbacks and no call at the token cap, else the cell is skipped.

Pass bar: the screen bar in `st-baseline/PLAN.md`.
