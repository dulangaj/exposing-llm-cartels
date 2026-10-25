import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("figure", Path(__file__).parents[1] / "trials/main-study/figure.py")
fig = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fig)


class FigureTest(unittest.TestCase):
    def test_svg_from_counts(self):
        by = {a: {d: (3, 24) for d, _ in fig.DETS} for a, _ in fig.ARMS}
        s = fig.svg(by)
        self.assertTrue(s.startswith("<svg") and s.rstrip().endswith("</svg>"))
        self.assertEqual(s.count("<circle"), len(fig.ARMS) * len(fig.DETS))

    def test_real_runs_have_24_seeds_per_arm(self):
        by = fig.rates()
        self.assertEqual({v[1] for a in by.values() for v in a.values()}, {24})

    def test_primary_panel_matches_primary_py(self):
        root = Path(__file__).parents[1]
        out = subprocess.run([sys.executable, "trials/main-study/primary.py", *map(str, fig.RUNS), "--pos", "P,W", "--neg", "B,C,D"],
                             cwd=root, capture_output=True, text=True, check=True).stdout
        want = {l.split(":")[0]: int(l.split()[1].split("/")[0]) for l in out.splitlines() if l[1:2] == ":"}
        by = fig.rates()
        self.assertEqual({a: by[a]["price_overreact"][0] for a in want}, want)
