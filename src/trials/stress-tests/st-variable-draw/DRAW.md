# Random draw of stress-test variables

Two assistants independently listed variables that could break the main-study result: list A (22) and list B (25). `random.Random(1792894874)`: `sample(range(1, 23), 3)` from A = [3, 20, 21]; `sample(range(1, 26), 6)` from B = [17, 15, 16, 7, 11, 22], of which the first three distinct from the A picks were taken.

| Drawn | Variable | Folder |
|---|---|---|
| A 3 | Activation probe on the firm | `st-activation-probe/` |
| A 20 | Judge identity and view | `st-judge-swap/` |
| A 21 | Paraphrased message channel | `st-paraphrase/` |
| B 17 | Context position, message order, delivery delay | `st-history-order/` |
| B 15 | Reasoning mode and token allowance | `st-reasoning-off/` |
| B 16 | History length and private-plan persistence | `st-short-history/` |

List A: 1 what the detector leaks to the agents; 2 log-prob signal at the reaction round; 3 activation probe on the firm; 4 demand noise; 5 number of firms; 6 probe depth and repetition; 7 round of the probe in the finite horizon; 8 memory window and history order; 9 thinking on/off and token cap; 10 sampling temperature; 11 test-retest reliability; 12 quantization; 13 prompt language; 14 system-prompt persona; 15 model's knowledge of antitrust law; 16 monitor feedback loop; 17 model heterogeneity across the two firms; 18 price scale and round-number anchoring; 19 number formatting; 20 judge identity and view; 21 message protocol and paraphrased channel; 22 private plan channel.

List B: 1 whether profitable defection is observable; 2 agreement target and partner membership; 3 private cost and demand information; 4 number of firms and coalition size; 5 demand noise and observation precision; 6 remaining horizon and relative patience; 7 system persona and objective wording; 8 antitrust information versus audit salience; 9 temperature, top-p and top-k; 10 decoder seeds, batching and request order; 11 quantization precision; 12 model pairing and capability asymmetry; 13 prompt language and code-switching; 14 numeric representation and tokenizer quirks; 15 reasoning mode, token allowance and truncation; 16 history length and private-plan persistence; 17 context position, message order and delivery delay; 18 shared conventions and channel capacity; 19 where communication is interrupted; 20 auditor identity, model family and stated allegiance; 21 detector disclosure, feedback and adaptation budget; 22 auditor access and evidence combination; 23 log-probabilities of unchosen prices; 24 activation layer, token position and instruction leakage; 25 probe depth, sign, timing and attributed cause.
