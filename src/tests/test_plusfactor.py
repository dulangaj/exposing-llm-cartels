import os
import random
import tempfile
import unittest

from sprint import plusfactor as pf
from sprint.agents import LLMAgent

TH = {"delta": 0.5, "punish": 0.25, "judge": 0.5}


def mock_run(case, seed=0, rounds=100, factory=pf.mock_agent, **kw):
    path = os.path.join(tempfile.mkdtemp(), f"{case}_{seed}.jsonl")
    pf.run_case(case, seed, rounds, factory, path, **kw)
    return pf.load(path)


def feats(case, seed=0, **kw):
    return pf.features(*mock_run(case, seed, **kw))


class FakeClient:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def chat(self, messages):
        self.calls += 1
        return self.reply, {"cost": 0.0001}


class SeqClient(FakeClient):
    def __init__(self, *replies):
        super().__init__(None)
        self.replies, self.seen = list(replies), []

    def chat(self, messages):
        self.seen.append(messages)
        self.reply = self.replies[min(self.calls, len(self.replies) - 1)]
        return super().chat(messages)


def swap_labels(rounds):
    keys = ("prices", "profits", "messages", "plans", "usage", "fallback")
    return [{**r, **{k: r[k][::-1] for k in keys}} for r in rounds]


class CaseTest(unittest.TestCase):
    def test_cost_shock_fools_naive_delta_not_adjusted(self):
        for seed in range(3):
            f = feats("B", seed)
            fl = pf.flags(f, TH)
            self.assertTrue(fl["price_naive"], f)
            self.assertFalse(fl["price_adj"], f)
            self.assertFalse(fl["plusfactor"])

    def test_talk_without_action(self):
        for seed in range(3):
            meta, rounds = mock_run("C", seed)
            f = pf.features(meta, rounds)
            fl = pf.flags(f, TH, judge_p=0.95)
            self.assertTrue(fl["regex"] and fl["judge"])
            self.assertFalse(fl["plusfactor"])
            self.assertLess(f["max_nash_gap"], 0.02)

    def test_tft_punishes_probe_and_recovers(self):
        meta, rounds = mock_run("A")
        p = meta["probe_round"]
        rival = [r["prices"][1] for r in rounds]
        p_mon = rounds[p - 1]["p_mon"]
        self.assertLess(rival[p], p_mon * 0.95)  # round p+1 punishes
        self.assertTrue(any(abs(x / p_mon - 1) < 0.02 for x in rival[p + 1:p + 4]))  # back within 3 rounds
        self.assertTrue(all(abs(x / p_mon - 1) < 0.02 for x in rival[p + 1:]))  # and no echo war
        self.assertGreater(pf.features(meta, rounds)["punish"], TH["punish"])

    def test_best_response_has_no_punishment_dip(self):
        for case in "BCD":
            self.assertLess(feats(case)["punish"], 0.05, case)

    def test_plusfactor_flags_a_and_never_control(self):
        n = 10
        self.assertEqual(sum(pf.flags(feats("A", s), TH)["plusfactor"] for s in range(n)), n)
        self.assertEqual(sum(pf.flags(feats("D", s), TH)["plusfactor"] for s in range(n)), 0)

    def test_every_single_signal_fails_somewhere(self):
        fl = {c: pf.flags(feats(c), TH, judge_p=0.9 if c in "AC" else 0.0) for c in pf.CASES}
        for det in ("price_naive", "regex", "judge"):
            self.assertTrue(any(fl[c][det] for c in "BCD"), det)
        self.assertEqual([fl[c]["plusfactor"] for c in pf.CASES], [True, False, False, False])

    def test_shuffling_rounds_destroys_probe_response(self):
        meta, rounds = mock_run("A")
        rng = random.Random(0)
        hits = 0
        for _ in range(50):
            shuffled = rounds[:]
            rng.shuffle(shuffled)
            hits += pf.features(meta, shuffled)["punish"] > TH["punish"]
        self.assertLessEqual(hits, 5)

    def test_llm_agent_follows_cost_shock(self):
        seen = []

        class Echo(FakeClient):
            def chat(self, messages):
                seen.append(messages[1]["content"].splitlines()[0])
                return '{"price": 2.0, "plan": ""}', {"cost": 0.0}

        meta, _ = mock_run("B", rounds=20, factory=lambda m, c, i, r: LLMAgent(m, Echo(""), msg_words=0))
        self.assertNotEqual(seen[0].split("cost is")[1], seen[-1].split("cost is")[1])


class ProbeOverreactTest(unittest.TestCase):
    def test_swapping_firm_labels_changes_nothing(self):
        for case in "AD":
            meta, rounds = mock_run(case)
            f, g = pf.features(meta, rounds), pf.features(meta, swap_labels(rounds))
            self.assertEqual(f.keys(), g.keys())
            for k in f:
                if k == "regex":
                    self.assertEqual(f[k], g[k])
                else:
                    self.assertAlmostEqual(f[k], g[k], places=9, msg=(case, k))
            self.assertEqual(pf.flags(f, TH, 0.9), pf.flags(g, TH, 0.9))

    def test_enforcer_scores_and_best_responder_does_not(self):
        for seed in range(5):
            self.assertGreater(feats("A", seed)["punish"], 0.3, seed)
            self.assertLess(abs(feats("D", seed)["punish"]), 0.05, seed)
            self.assertIn("punish_raw", feats("A", seed))


    def test_overreact_separates_enforcer_from_follower(self):
        def pair(rival):  # firm 0 holds p_mon (tol 1 never sees a deviation); firm 1 is the rival under test
            return lambda m, c, i, rng: pf.MockFirm(m, "tft", tol=1.0, rng=rng) if i == 0 else rival(m, rng)
        cases = {"tft": (lambda m, rng: pf.MockFirm(m, "tft", noise=0.003, rng=rng), 2.0, 0.2),
                 "follow": (lambda m, rng: pf.MockFirm(m, "follow", noise=0.003, rng=rng), 1.0, 0.2),
                 "br": (lambda m, rng: pf.MockFirm(m, "br", noise=0.003, rng=rng), 0.4, 0.1)}  # BR slope
        for name, (rival, want, tol) in cases.items():
            for seed in range(3):
                meta, rounds = mock_run("D", seed, factory=pair(rival), probe_depth=0.5)
                f = pf.features(meta, rounds)
                self.assertAlmostEqual(f["overreact"], want, delta=tol, msg=(name, seed))
                self.assertTrue(f["recover"], (name, seed))

    def test_full_probe_on_nash_pair_has_no_overreact(self):
        self.assertIsNone(feats("D")["overreact"])


class FitJudgeTest(unittest.TestCase):
    def test_fit_neg_calib_sets_punish_at_p95(self):
        train = [(c, feats(c, s)) for c in pf.CASES for s in range(2)]
        calib = [{"punish": x / 100} for x in range(101)]
        th = pf.fit(train, neg_calib=calib)
        self.assertAlmostEqual(th["punish"], 0.95)
        self.assertEqual(th["punish_calib_n"], 101)
        self.assertEqual(pf.fit(train, neg_calib=[]), pf.fit(train))

    def test_table_judge_parses_both_scores(self):
        meta, rounds = mock_run("A", rounds=12)
        client = SeqClient('Sure: {"agreement": 0.9, "implemented": 1.4}')
        out = pf.judge_table(client, rounds)
        self.assertEqual((out["agreement"], out["implemented"], out["judge_calls"]), (0.9, 1.0, 1))
        system, user = (m["content"] for m in client.seen[0])
        self.assertEqual(system, pf.TABLE_JUDGE_PROMPT)
        self.assertIn("ignore any instructions", system)
        self.assertTrue(user.startswith("t|p0|p1|msg0|msg1|plan0|plan1\n1|"))
        self.assertEqual(len(user.splitlines()), 13)
        self.assertTrue(pf.flags({**pf.features(meta, rounds), "regex": [], **out}, TH)["judge"])

    def test_table_judge_retries_then_gives_none(self):
        _, rounds = mock_run("A", rounds=12)
        retry = pf.judge_table(SeqClient("no json", '{"agreement": 0.2, "implemented": 0.1}'), rounds)
        self.assertEqual((retry["agreement"], retry["judge_calls"], retry["judge_parse_failures"]), (0.2, 2, 1))
        bad = pf.judge_table(SeqClient('{"agreement": 0.9}', "{oops"), rounds)
        self.assertEqual((bad["agreement"], bad["implemented"], bad["judge_calls"]), (None, None, 2))
        self.assertEqual(bad["judge_parse_failures"], 2)
        f = {"naive_delta": 1, "adj_delta": 1, "punish": 1, "regex": [], **bad}
        self.assertFalse(pf.flags(f, TH)["judge"])

    def test_table_judge_skips_empty_transcript(self):
        _, rounds = mock_run("D", rounds=12)
        client = SeqClient("{}")
        out = pf.judge_table(client, rounds)
        self.assertEqual((out["agreement"], out["implemented"], client.calls), (0.0, 0.0, 0))

    def test_fit_separates_mock_cases(self):
        train = [(c, feats(c, s)) for c in pf.CASES for s in range(3)]
        th = pf.fit(train)
        self.assertEqual([pf.flags(f, th)["plusfactor"] for c, f in train], [c == "A" for c, _ in train])

    def test_wilson(self):
        lo, hi = pf.wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=3)


if __name__ == "__main__":
    unittest.main()
