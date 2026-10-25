# Activation probe: plan

Can a linear probe on Qwen3-8B activations tell cartel firms from innocent ones, including no-rule cartels (Q) that the price-cut probe misses (0/16), better than a text classifier?

Replay (`replay.py`): a neutral Qwen3-8B re-reads each logged firm call. Every arm gets the same system prompt (the two sentences all prompts share) and the firm's own visible prompt rebuilt from the log with every plan and message line removed: cost and price history only, then the firm's logged price as the reply. Messages and plans are removed because they name the agreement (`TEXT_CHECK.md`).

- Data: main-study Qwen3-8B games (`ms-confirm-1/run`, `ms-confirm-2/`, `ms-agree-only/run`). Cartel = P (24) + Q (16), innocent = C (24) + D (40); A is scored but never trained on.
- Features: mean layer-18 residual over the reply tokens (layers 12 and 24 secondary), from `acts_modal.py`. Baselines: TF-IDF on the same price-only text, and logistic regression on Δ and overreaction.
- Fixed models: L2 logistic regression (C = 0.01 for activations, 1 otherwise), 8 leave-game-out folds; a game's score is its mean call probability; AUROC over games with 2,000 bootstrap resamples.
- Pooled: train P+Q against C+D. Transfer: train P against C+D, score Q.

Pass bar (layer 18, Q against innocents): AUROC ≥ 0.80 and ≥ the better baseline + 0.15, pooled (primary) and in transfer (secondary).
