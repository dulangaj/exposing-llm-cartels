#!/bin/bash
# Stress-test screens: warmup, then every cell in sequence.
# Dry run offline: S=$TMPDIR/s M=--mock WARM=: bash trials/stress-tests/batch.sh
S=${S:-trials/stress-tests/st-screen-runs}; mkdir -p $S
M=${M:-"--rounds 20 --firm-model modal:qwen3-8b --x-model modal:qwen3-8b --judge-model modal:qwen3-8b"}
${WARM:-python trials/main-study/warmup.py} || exit 1
cell() {  # cell <name> <seeds> <scenarios> <flags...>
  local name=$1 seeds=$2 scen=$3 O=$S/$1; shift 3; mkdir -p $O
  echo "cell $name: $*"
  python -m sprint.testset_run --phase test --seeds $seeds --scenarios $scen --out $O $M "$@" \
    --wall 1500 --judge-wall 300 --budget 100 --judge-budget 100 > /dev/null
}
cell baseline 300-307 P,Q,C --thinking
cell paraphrase 300-307 P,Q --thinking --paraphrase
cell oldest-first 300-307 P,Q,C --thinking --oldest-first
cell delay-1 300-307 P,Q,C --thinking --delay 1
if cell reasoning-off-preflight 299 P && python - $S/reasoning-off-preflight <<'PY'
import glob, json, sys
r = [x for f in glob.glob(sys.argv[1] + "/P_seed299.jsonl") for x in map(json.loads, open(f)) if x["type"] == "round"]
mx = max(u.get("completion_tokens", 0) for x in r for u in x["usage"]); fb = sum(sum(x["fallback"]) for x in r)
print(f"preflight: {len(r)} rounds, max completion tokens {mx} of 2048, fallbacks {fb}")
sys.exit(0 if len(r) == 20 and mx < 2048 and fb == 0 else 1)
PY
then cell reasoning-off 300-307 P,Q,C
else echo "preflight failed; reasoning-off skipped"; fi
cell window-3 300-307 P,Q,C --thinking --window 3
cell no-plan 300-307 P,Q,C --thinking --no-plan
