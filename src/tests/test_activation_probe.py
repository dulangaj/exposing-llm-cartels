"""Activation-probe replay builder (stdlib) and analysis on fake activations (needs numpy + scikit-learn, else skipped):
uv run --no-project --with numpy --with scikit-learn python -m unittest tests.test_activation_probe"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from sprint.plusfactor import load

PROBE = Path(__file__).resolve().parents[1] / "trials/stress-tests/st-activation-probe"
sys.path.insert(0, str(PROBE))
import replay  # noqa: E402

HAVE_SK = all(importlib.util.find_spec(m) for m in ("numpy", "sklearn"))


class ReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = replay.build()
        cls.by_id = {r["id"]: r for r in cls.rows}

    def test_rebuilt_prompts_match_logged_probe_prompts(self):
        n = 0
        for d in replay.RUNS:
            for path in sorted((replay.ROOT / d).glob("*_seed*.jsonl")):
                meta, rounds = load(path)
                for r in rounds:
                    row = self.by_id.get(f"{meta['case']}{meta['seed']}-f1-t{r['t']}")
                    if "probe_prompt" in r and row:
                        self.assertEqual(row["user"], replay.price_only(r["probe_prompt"]["user"]))
                        n += 1
        self.assertGreater(n, 100)

    def test_neutral_system_prompt_and_no_forced_or_fallback_calls(self):
        self.assertEqual({r["system"] for r in self.rows}, {replay.NEUTRAL})
        meta, rounds = load(replay.ROOT / replay.RUNS[0] / "P_seed108.jsonl")
        probe = next(r for r in rounds if r["probe"])
        self.assertNotIn(f"P108-f0-t{probe['t']}", self.by_id)
        self.assertIn(f"P108-f1-t{probe['t']}", self.by_id)
        fb = [(f"{m['case']}{m['seed']}-f{i}-t{r['t']}") for d in replay.RUNS
              for p in (replay.ROOT / d).glob("*_seed*.jsonl") for m, rs in [load(p)] if m["case"] in replay.ARMS
              for r in rs for i in (0, 1) if r["fallback"][i]]
        self.assertTrue(fb)
        self.assertFalse(set(fb) & set(self.by_id))

    def test_prices_only_no_plans_or_messages(self):
        for r in self.rows:
            self.assertEqual(list(__import__("json").loads(r["output"])), ["price"])
            self.assertNotIn("plan", r["user"])
            self.assertNotIn("essage", r["user"])
        self.assertEqual({tuple(sorted(r)) for r in self.rows}, {tuple(sorted(self.rows[0]))})


def fake(n_games=10, calls=6, signal=0.0, dim=16, seed=0):
    """Fake replay rows and activations; cartel arms' activations shift by `signal` along one direction."""
    import numpy as np
    rng = np.random.default_rng(seed)
    rows, X = [], []
    for arm in ("P", "Q", "C", "D", "A"):
        for s in range(n_games):
            for c in range(calls):
                rows.append({"game": f"{arm}{s}", "arm": arm, "user": "round history price",
                             "adj_delta": float(rng.normal()), "overreact": None if c == 0 else float(rng.normal()),
                             "output": " ".join(rng.choice(["hold", "price", "plan", "market", "cost"], 5))})
                X.append(rng.normal(size=dim) + signal * (arm in "PQ") * np.eye(dim)[0])
    return rows, np.array(X, dtype=np.float32)


@unittest.skipUnless(HAVE_SK, "needs numpy and scikit-learn")
class AnalysisTest(unittest.TestCase):
    def run_fake(self, signal):
        import analyze
        import numpy as np
        rows, X = fake(signal=signal)
        with tempfile.TemporaryDirectory() as d:
            Path(d, "replay.jsonl").write_text("".join(__import__("json").dumps(r) + "\n" for r in rows))
            for L in analyze.LAYERS:
                np.save(Path(d, f"part000_L{L}.npy"), X[:len(X) // 2].astype(np.float16))
                np.save(Path(d, f"part001_L{L}.npy"), X[len(X) // 2:].astype(np.float16))
            rows, acts = analyze.load(d)
        res = analyze.run(rows, acts)
        return analyze, res

    def test_signal_is_found_and_beats_text(self):
        analyze, res = self.run_fake(signal=3.0)
        self.assertGreater(res["act_L18"]["Q_vs_innocent"][0], 0.95)
        self.assertGreater(res["act_L18"]["transfer_Q_vs_innocent"][0], 0.95)
        self.assertTrue(analyze.verdict(res, "Q_vs_innocent")[0])
        self.assertIn("Noticeable (primary): YES", analyze.report(res, 1, 1))

    def test_no_signal_is_chance(self):
        analyze, res = self.run_fake(signal=0.0)
        self.assertLess(abs(res["act_L18"]["cartel_vs_innocent"][0] - 0.5), 0.25)
        self.assertFalse(analyze.verdict(res, "Q_vs_innocent")[0])

    def test_folds_hold_out_whole_games(self):
        import analyze
        rows, _ = fake()
        arm_of = {r["game"]: r["arm"] for r in rows}
        held = analyze.folds(set(arm_of), arm_of)
        self.assertEqual(len(held), analyze.FOLDS)
        self.assertEqual(set().union(*held), set(arm_of))
        self.assertEqual(sum(map(len, held)), len(arm_of))


if __name__ == "__main__":
    unittest.main()
