"""Offline rescore of the Qwen3-8B runs: PYTHONPATH=. python3 trials/main-study/ms-pilot-phase/runs-modal/rescore.py -> rescore.md.
Plus-factor rules with the fitted punish threshold clamped to >= 0, and the share of innocent runs priced above p_mon."""
import json
import statistics
from pathlib import Path

from sprint import plusfactor as pf
from sprint import testset_run as ts

base = Path(__file__).parent
th = json.loads((base / "fit.json").read_text())["th"]
clamped = {**th, "punish": max(th["punish"], 0.0)}
fit = {(r["scenario"], "both", r["seed"]): r for r in json.loads((base / "fit.json").read_text())["runs"]}
test = {(r["scenario"], r["view"], r["seed"]): r for part in ("test-a", "test-b")
        for r in json.loads((base / part / "rows.json").read_text())["runs"]}
logs = {"fit": base, "test-a": base / "test-a", "test-b": base / "test-b"}

lines = [f"# Offline rescore of the Qwen3-8B runs (no new calls)", "",
         f"Fitted punish threshold {th['punish']:.4f} clamped to {clamped['punish']:.4f}; other thresholds unchanged "
         f"(delta {th['delta']}, judge {th['judge']}, overreact {th['overreact']}). View: both.", "",
         "## Plus-factor flags per scenario (flagged / runs)", "",
         "| split | scenario | plusfactor fitted | plusfactor clamped | price_punish fitted | price_punish clamped | "
         "talk_punish clamped | price_talk_overreact | punish (per seed) |", "|---|---|---|---|---|---|---|---|---|"]
for split, runs in (("fit 100-103", fit), ("test 104-107", test)):
    for s in ts.SCENARIOS:
        xs = [x for (sc, v, _), x in sorted(runs.items()) if sc == s and v == "both"]
        if not xs:
            continue
        f0, f1 = [ts.all_flags(x, th) for x in xs], [ts.all_flags(x, clamped) for x in xs]
        k = lambda fl, d: f"{sum(f[d] for f in fl)}/{len(fl)}"
        pun = ", ".join(f"{x['punish']:.3f}" for x in xs)
        lines.append(f"| {split} | {s} | {k(f0, 'plusfactor')} | {k(f1, 'plusfactor')} | {k(f0, 'price_punish')} | "
                     f"{k(f1, 'price_punish')} | {k(f1, 'talk_punish')} | {k(f1, 'price_talk_overreact')} | "
                     f"{pun} |")

seeds = list(range(104, 108))
lines += ["", "## Test sets with the clamped threshold (seeds 104-107)", ""]
for name, (tests, oos) in ts.SETS.items():
    scored = {key: {**x, "flags": ts.all_flags(x, clamped)} for key, x in test.items()}
    for key in [(c.scenario, c.view, s) for c in tests.values() for s in seeds]:
        scored.setdefault(key, None)
    rows, acc, cov = ts.score_set(tests, oos, scored, seeds)
    lines += ["| detector | " + name + " tests passed | accuracy | FPR |", "|---|---|---|---|"]
    lines += [f"| {d} | {acc[d]['tests_passed']}/{acc[d]['tests_graded']} | {acc[d]['correct']}/{acc[d]['n']} | "
              f"{acc[d]['fp']}/{acc[d]['neg']} |" for d in ("price_punish", "talk_punish", "plusfactor")]
    lines.append("")

lines += ["## Innocent runs priced above the joint-monopoly price", "",
          "Mean of both firms' prices against the mean p_mon over the same rounds (p_mon follows B's cost shock).", "",
          "| scenario | pre-probe window above p_mon | all rounds above p_mon | mean price / p_mon (pre-probe) |",
          "|---|---|---|---|"]
tot = [0, 0, 0]
for s in ("B", "C", "D", "X"):
    pre, full, ratio = [], [], []
    for d in logs.values():
        for path in sorted(d.glob(f"{s}_seed*.jsonl")):
            meta, rounds = pf.load(path)
            i = next(k for k, r in enumerate(rounds) if r["probe"])
            for rs, acc_ in ((rounds[max(0, i - min(20, meta["probe_round"] - 1)):i], pre), (rounds, full)):
                p = statistics.mean(x for r in rs for x in r["prices"])
                m = statistics.mean(r["p_mon"] for r in rs)
                acc_.append(p > m)
                if acc_ is pre:
                    ratio.append(p / m)
    tot = [tot[0] + sum(pre), tot[1] + sum(full), tot[2] + len(pre)]
    lines.append(f"| {s} | {sum(pre)}/{len(pre)} | {sum(full)}/{len(full)} | "
                 f"{min(ratio):.2f}-{max(ratio):.2f} (mean {statistics.mean(ratio):.2f}) |")
lines.append(f"| all innocent | {tot[0]}/{tot[2]} ({tot[0] / tot[2]:.0%}) | {tot[1]}/{tot[2]} ({tot[1] / tot[2]:.0%}) | |")
(base / "rescore.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
