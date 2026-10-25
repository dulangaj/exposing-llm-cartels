#!/bin/bash
# Follow-up runs: trials/stress-tests/xbatch.sh 8b|14b|no-price-replication <out dir>
# (14b needs CS_MODEL=Qwen/Qwen3-14B-FP8 CS_SERVED=qwen3-14b on the server, see modal_app/README.md).
S=${2:?out dir}; mkdir -p $S; MD=${CS_SERVED:-qwen3-8b}
M=${M:-"--rounds 20 --firm-model modal:$MD --x-model modal:$MD --judge-model modal:$MD"}
${WARM:-python trials/main-study/warmup.py} || exit 1
cell() {  # cell <name> <seeds> <scenarios> <flags...>
  local name=$1 seeds=$2 scen=$3 O=$S/$1; shift 3; mkdir -p $O
  echo "cell $name: $*"
  python -m sprint.testset_run --phase test --seeds $seeds --scenarios $scen --out $O $M \
    --wall 1500 --judge-wall 300 --budget 100 --judge-budget 100 "$@" > /dev/null
}
preflight() {  # one reasoning-off P game must finish with no fallbacks and no call at the 2048-token cap
  cell $1 399 P && python - $S/$1 <<'PY'
import glob, json, sys
r = [x for f in glob.glob(sys.argv[1] + "/P_seed399.jsonl") for x in map(json.loads, open(f)) if x["type"] == "round"]
mx = max(u.get("completion_tokens", 0) for x in r for u in x["usage"]); fb = sum(sum(x["fallback"]) for x in r)
print(f"preflight: {len(r)} rounds, max completion tokens {mx} of 2048, fallbacks {fb}")
sys.exit(0 if len(r) == 20 and mx < 2048 and fb == 0 else 1)
PY
}
if [ "$1" = 8b ]; then
  cell reasoning-off 400-415 P,Q,C,D
  cell probe-depth-1 400-415 P,C,D --probe-depth 1.0
  cell reprobe 400-415 P,C,D --reprobe 3
  cell no-price 400-415 P,Q,C,D --thinking --no-number --wall 2700
elif [ "$1" = no-price-replication ]; then  # st-no-price-replication/games/ holds both batches' games
  cell batch-416-431 416-431 P,Q,C,D --thinking --no-number --wall 2700
  cell batch-432-447 432-447 P,Q,C,D --thinking --no-number --wall 2700
elif [ "$1" = 14b ]; then
  if preflight preflight-14b; then cell reasoning-off-14b 400-407 P,C; else echo "14b preflight failed; reasoning-off-14b skipped"; fi
fi
