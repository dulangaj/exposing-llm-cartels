import unittest

from sprint.econ import Market, collusion_index


class EconTest(unittest.TestCase):
    def test_calvano_benchmarks(self):
        b = Market(alpha=1).benchmarks()
        self.assertAlmostEqual(b["p_nash"], 1.4729, places=3)
        self.assertAlmostEqual(b["p_mon"], 1.9250, places=3)

    def test_alpha_scales_prices(self):
        self.assertAlmostEqual(Market(alpha=3.2).nash_price(), 3.2 * Market().nash_price(), places=6)

    def test_delta_endpoints(self):
        b = Market(alpha=10).benchmarks()
        self.assertAlmostEqual(collusion_index(b["pi_nash"], b["pi_nash"], b["pi_mon"]), 0)
        self.assertAlmostEqual(collusion_index(b["pi_mon"], b["pi_nash"], b["pi_mon"]), 1)


if __name__ == "__main__":
    unittest.main()
