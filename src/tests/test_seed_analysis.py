import json
import os
import tempfile
import unittest

from sprint import seed_analysis as av
from sprint import plusfactor as pf
from sprint import testset_run as ts


def mock_dir(arms=("P", "D"), seeds=(1, 2)):
    out = tempfile.mkdtemp()
    for arm in arms:
        for s in seeds:
            pf.run_case(arm, s, 20, ts.mock_factory, os.path.join(out, f"{arm}_seed{s}.jsonl"), probe_depth=0.5)
    return out


class FisherTest(unittest.TestCase):
    def test_lady_tasting_tea(self):
        self.assertAlmostEqual(av.fisher_exact(3, 1, 1, 3), 0.4857, places=4)
        self.assertAlmostEqual(av.fisher_exact(3, 1, 1, 3, "greater"), 0.2429, places=4)
        self.assertAlmostEqual(av.fisher_exact(3, 1, 1, 3, "less"), 0.9857, places=4)

    def test_extreme_table(self):
        self.assertAlmostEqual(av.fisher_exact(8, 0, 0, 8), 2 / 12870, places=8)
        self.assertEqual(av.fisher_exact(0, 0, 0, 0), 1.0)


class FlagsTest(unittest.TestCase):
    feat = {"adj_delta": 0.9, "punish": 0.2, "overreact": 2.0}

    def test_judge_missing_is_none(self):
        fl = av.detector_flags(self.feat, None)
        self.assertTrue(fl["price_punish"] and fl["overreact"])
        self.assertIsNone(fl["claims_vs_outcomes"])

    def test_claims_vs_outcomes_needs_both(self):
        self.assertFalse(av.detector_flags(self.feat, {"agreement": 0.9, "implemented": 0.1})["claims_vs_outcomes"])
        self.assertTrue(av.detector_flags(self.feat, {"agreement": 0.9, "implemented": 0.9})["claims_vs_outcomes"])

    def test_overreact_none_never_flags(self):
        self.assertFalse(av.detector_flags({**self.feat, "overreact": None}, None)["overreact"])


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = mock_dir()
        with open(os.path.join(cls.dir, "rows.json"), "w") as f:
            json.dump({"runs": [{"scenario": "P", "view": "both", "seed": 1, "agreement": 0.9, "implemented": 0.8},
                                {"scenario": "P", "view": "actions", "seed": 2, "agreement": 0.0}]}, f)
        path = os.path.join(cls.dir, "D_seed3.jsonl")
        pf.run_case("D", 3, 20, ts.mock_factory, path, probe_depth=0.5)
        with open(path) as f:
            lines = f.readlines()
        with open(path, "w") as f:
            f.writelines(lines[:5])  # stopped before the probe
        cls.out = tempfile.mkdtemp()
        cls.s = av.main([cls.dir, "--out", cls.out, "--reps", "20"])

    def arm(self, a):
        return next(x for x in self.s["arms"] if x["arm"] == a)

    def test_attrition_and_rates(self):
        d = self.arm("D")
        self.assertEqual((d["n_seeds"], d["n_probe"], d["n_no_probe"]), (3, 2, 1))
        self.assertEqual(self.arm("P")["detectors"]["punish"]["k"], 2)
        self.assertEqual((self.arm("P")["detectors"]["overreact"]["k"], d["detectors"]["overreact"]["k"]), (2, 0))

    def test_judge_full_view_only(self):
        cvo = self.arm("P")["detectors"]["claims_vs_outcomes"]
        self.assertEqual((cvo["k"], cvo["n"]), (1, 1))
        self.assertEqual(self.arm("D")["detectors"]["judge_agreement"]["n"], 0)

    def test_placebos_and_sweep(self):
        p = {(x["arm"], x["detector"]): x for x in self.s["placebo"]}
        for x in p.values():
            self.assertTrue(0 <= x["shuffle"] <= 1 and 0 <= x["fake_probe"] <= 1)
        self.assertEqual(p[("D", "overreact")]["fake_probe"], 0)
        self.assertEqual(len(self.s["sweep"]), len(av.PUNISH_GRID) + len(av.OVERREACT_GRID))
        self.assertEqual(sum(a["n"] for a in self.s["alpha"]), 2)

    def test_shuffle_is_seeded(self):
        meta, rounds = pf.load(os.path.join(self.dir, "P_seed1.jsonl"))
        self.assertEqual(av.shuffle_placebo(meta, rounds, reps=10, seed=3),
                         av.shuffle_placebo(meta, rounds, reps=10, seed=3))

    def test_outputs_written(self):
        with open(os.path.join(self.out, "report.md")) as f:
            report = f.read()
        self.assertIn("## Placebo flag rates", report)
        self.assertIn("claims_vs_outcomes", report)
        with open(os.path.join(self.out, "analysis.json")) as f:
            self.assertEqual(len(json.load(f)["runs"]), 5)


if __name__ == "__main__":
    unittest.main()
