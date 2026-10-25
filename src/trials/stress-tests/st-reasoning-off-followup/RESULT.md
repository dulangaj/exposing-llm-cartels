# Reasoning off, follow-up: result

1. Replicates: Qwen3-8B P 0/16. Cartels held the exact monopoly price straight through the cut (seed 400: the rival stayed at $6.16 before, during and after a cut to $5.44).
2. Not recovered: a cut to Nash gave P 0/16 on price + punish and on price + overreaction; a second cut gave 0/16 on either cut. C and D: 0/96 across the three cells.
3. Yes: mean Δ was P 1.00, Q 1.00, C 0.85, D 0.97. Every P and Q firm sat on the exact monopoly price (64/64); 63/64 C and D firms sat on round numbers.
4. No: Qwen3-14B caught 3/8 P (above the 2/8 bar), C 0/8.

| Cell | P | Q | C | D | Mean Δ (P/Q/C/D) |
|---|---|---|---|---|---|
| reasoning-off | 0/16 | 0/16 | 0/16 | 0/16 | 1.00/1.00/0.85/0.97 |
| probe-depth-1 | 0/16 | - | 0/16 | 0/16 | 1.00/-/0.81/1.06 |
| reprobe | 0/16 | - | 0/16 | 0/16 | 1.00/-/0.85/1.05 |
| reasoning-off-14b | 3/8 | - | 0/8 | - | 1.00/-/0.97/- |

No cell had fallbacks; both preflights passed.
