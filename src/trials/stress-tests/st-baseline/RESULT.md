# Screen baseline: result

The main study reproduces: P 8/8, Q 0/8, C 0/8 (mean Δ 1.00 / 1.00 / 0.50).

The stated price leaks the label: every P and Q firm's most common price is the exact monopoly price the prompt states (16/16 firms each), while 14/16 C firms sit on round numbers (`python3 trials/stress-tests/xread.py trials/stress-tests/st-screen-runs/baseline`). C's Δ is bimodal: 0.07-0.29 in five seeds, 0.86-1.21 in three.
