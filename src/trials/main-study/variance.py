"""Paper §4.1 and Appendix D over-reaction spread on ms-confirm-2 (cartel vs innocent games). Run from src/: python3 trials/main-study/variance.py"""
import glob, json, sys
sys.path.insert(0, ".")
from sprint import plusfactor as pf

cartel, innocent = [], []
for d in ("run-116-123", "run-124-131"):
    for f in sorted(glob.glob(f"trials/main-study/ms-confirm-2/{d}/*_seed*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        ft = pf.features(rows[0], [r for r in rows if r.get("type") == "round"])
        arm = f.split("/")[-1].split("_")[0]
        if arm in "PW": cartel.append(ft["overreact"])
        elif arm in "BCD": innocent.append((ft["overreact"], ft["adj_delta"]))
c = [x for x in cartel if x is not None]
print("cartel games", len(cartel), "defined", len(c), "min", min(c), "max", max(c))
d = [x for x in innocent if x[0] is not None]
print("innocent total", len(innocent), "defined", len(d), "undefined", len(innocent) - len(d))
print("zeros", sum(1 for o, _ in d if o == 0), "<=0.39", sum(1 for o, _ in d if o <= 0.39),
      "above1.5", [(round(o, 2), round(a, 2)) for o, a in d if o > 1.5])
