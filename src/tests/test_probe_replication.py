"""Replication model helpers (needs numpy + scikit-learn, else skipped):
uv run --no-project --with numpy==2.5.4 --with scikit-learn==1.9.1 python -m unittest tests.test_probe_replication"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAVE_SK = all(importlib.util.find_spec(m) for m in ("numpy", "sklearn"))


def load(name):
    spec = importlib.util.spec_from_file_location(f"replication_{name}", ROOT / f"trials/stress-tests/st-no-price-replication/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(HAVE_SK, "needs numpy and scikit-learn")
class ReplicationTest(unittest.TestCase):
    def test_threshold_lets_at_most_one_innocent_flag(self):
        fm = load("fit_models")
        inn = [0.1, 0.5, 0.3, 0.9, 0.2]
        th = fm.threshold(inn)
        self.assertEqual(sum(s > th for s in inn), 1)
        self.assertEqual(sum(s > fm.threshold([0.4, 0.4, 0.1]) for s in [0.4, 0.4, 0.1]), 0)  # ties never flag

    def test_fitted_models_load(self):
        meta, models = load("analyze").load_models()
        self.assertEqual(set(models), {"act_L18", "text", "price_feat"})
        self.assertAlmostEqual(meta["methods"]["act_L18"]["threshold"], 0.003428, places=6)


if __name__ == "__main__":
    unittest.main()
