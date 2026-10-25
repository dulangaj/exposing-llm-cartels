# Primary readout: price_overreact per arm and one one-sided Fisher test (cartel arms vs innocent arms).
# python3 trials/main-study/primary.py <run dir>... --pos P,W --neg B,C,D
import argparse, glob, json, sys
sys.path.insert(0, ".")
from sprint import plusfactor as pf
from sprint.seed_analysis import fisher_exact
p = argparse.ArgumentParser(); p.add_argument("dirs", nargs="+"); p.add_argument("--pos", default="P,W"); p.add_argument("--neg", default="B,C,D")
a = p.parse_args()
th = pf.TH
arms = {}
for d in a.dirs:
    for f in sorted(glob.glob(d + "/*_seed*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        ft = pf.features(rows[0], [r for r in rows if r.get("type") == "round"])
        o = ft["overreact"]
        arms.setdefault(f.split("/")[-1].split("_")[0], []).append(ft["adj_delta"] > th["delta"] and o is not None and o > th["overreact"])
for k, v in sorted(arms.items()): print(f"{k}: {sum(v)}/{len(v)}")
pos = [x for k in a.pos.split(",") for x in arms.get(k, [])]; neg = [x for k in a.neg.split(",") for x in arms.get(k, [])]
print(f"TPR {sum(pos)}/{len(pos)}  FPR {sum(neg)}/{len(neg)}  one-sided Fisher p = "
      f"{fisher_exact(sum(pos), len(pos) - sum(pos), sum(neg), len(neg) - sum(neg), 'greater'):.2g}")
