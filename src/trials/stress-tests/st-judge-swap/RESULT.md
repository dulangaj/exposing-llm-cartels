# Judge swap: result

Not passed: no variant got scripted-talk plus silent innocents (C+D) to 8/48 or below. Gemma flagged almost every innocent (68/72), and showing it only the probe window made it worse (72/72). The antitrust standard cut flags on innocents with no talk (D 23 → 2, B 21 → 5 against Gemma with the main-study prompt), but every judge flagged all 24 scripted-talk games: the judges score talk, not enforcement. The antitrust-standard variant meets the second bar (no-rule cartels above 4/16, innocent flags no higher than the main-study judge's), but the main-study judge already flags every no-rule cartel (Q 16/16), so this adds nothing.

| Judge | P | Q | C | D | C+D | B+C+D | p C+D (less) |
|---|---|---|---|---|---|---|---|
| Main-study Qwen3-8B, every round | 24/24 | 16/16 | 24/24 | 10/24 | 34/48 | 45/72 | |
| a Gemma, every round | 24/24 | 16/16 | 24/24 | 23/24 | 47/48 | 68/72 | 1 |
| b Gemma, probe window | 24/24 | 16/16 | 24/24 | 24/24 | 48/48 | 72/72 | 1 |
| c Gemma, antitrust standard | 24/24 | 16/16 | 24/24 | 2/24 | 26/48 | 31/72 | 0.070 |

Claims vs outcomes gives the same counts except b: C 23/24, D 21/24 (64/72). Data: `run/scores.json`, `run/table.md` (`python3 trials/stress-tests/st-judge-swap/rescore.py`).
