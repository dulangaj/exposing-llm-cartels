"""Probe-transfer analysis on fake data (needs numpy + scikit-learn, else skipped):
uv run --no-project --with numpy --with scikit-learn python -m unittest tests.test_probe_transfer"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAVE_SK = all(importlib.util.find_spec(m) for m in ("numpy", "sklearn"))


def load_transfer():
    spec = importlib.util.spec_from_file_location("probe_transfer_analyze", ROOT / "trials/stress-tests/st-probe-transfer/analyze.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_acts(d, rows, X):
    import numpy as np
    d.mkdir(parents=True)
    (d / "replay.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for L in (12, 18, 24):
        np.save(d / f"part000_L{L}.npy", X.astype(np.float16))


def fake(seed0, n_games, signal, rng, calls=5, dim=16):
    import numpy as np
    rows, X = [], []
    for arm in "PQCD":
        for s in range(seed0, seed0 + n_games):
            for _ in range(calls):
                rows.append({"game": f"{arm}{s}", "arm": arm, "user": "history", "output": '{"price": 2.0}',
                             "adj_delta": float(rng.normal()), "overreact": float(rng.normal())})
                X.append(rng.normal(size=dim) + signal * (arm in "PQ") * np.eye(dim)[0])
    return rows, np.array(X)


def write_log(path, case, seed, modes, p_mon=1.92):
    """A 6-round log whose firms price at `modes`; firm 0 is forced to 1.00 at the probe row."""
    lines = [{"type": "meta", "case": case, "seed": seed}]
    for t in range(1, 7):
        probe = t == 4
        lines.append({"type": "round", "t": t, "probe": probe, "p_mon": p_mon,
                      "prices": [1.00 if probe else modes[0], modes[1]]})
    path.write_text("".join(json.dumps(x) + "\n" for x in lines))


@unittest.skipUnless(HAVE_SK, "needs numpy and scikit-learn")
class ProbeTransferTest(unittest.TestCase):
    def test_rules_follow_modal_prices(self):
        x = load_transfer()
        with tempfile.TemporaryDirectory() as d:
            write_log(Path(d, "P_seed400.jsonl"), "P", 400, (1.92, 1.80))
            write_log(Path(d, "C_seed400.jsonl"), "C", 400, (2.00, 1.50))
            write_log(Path(d, "Q_seed400.jsonl"), "Q", 400, (1.87, 2.00))
            r = x.rules(d)
        self.assertEqual(r["P400"], {"exact": 1.0, "nonround": 1.0})
        self.assertEqual(r["C400"], {"exact": 0.0, "nonround": 0.0})
        self.assertEqual(r["Q400"], {"exact": 0.0, "nonround": 1.0})

    def test_transfer_finds_a_shared_signal_and_rejects_overlap(self):
        import numpy as np
        x = load_transfer()
        rng = np.random.default_rng(0)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            write_acts(d / "train", *fake(100, 12, 3.0, rng))
            test_rows, X = fake(400, 8, 3.0, rng)
            write_acts(d / "test", test_rows, X)
            (d / "games").mkdir()
            for r in {r["game"]: r for r in test_rows}.values():
                write_log(d / "games" / f"{r['arm']}_seed{r['game'][1:]}.jsonl", r["arm"], int(r["game"][1:]),
                          (1.92, 1.92) if r["arm"] in "PQ" else (2.0, 2.0))
            res, n_train, n_test, games = x.run(d / "train", d / "test", d / "games")
            self.assertGreater(res["act_L18"]["Q_vs_innocent"][0], 0.95)
            self.assertEqual(res["rule_exact"]["Q_vs_innocent"][0], 1.0)
            self.assertLess(abs(res["text"]["Q_vs_innocent"][0] - 0.5), 0.3)
            self.assertTrue(x.verdicts(res)["activation_win"])
            self.assertIn("Activation win", x.report(res, n_train, n_test, games))
            write_acts(d / "overlap", *fake(100, 12, 3.0, rng))
            with self.assertRaises(AssertionError):
                x.run(d / "train", d / "overlap", d / "games")


if __name__ == "__main__":
    unittest.main()
