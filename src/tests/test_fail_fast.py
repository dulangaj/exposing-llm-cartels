import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from sprint import llm
from sprint import plusfactor as pf
from sprint import testset_run as ts
from sprint.agents import LLMAgent
from sprint.econ import Market


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


class FailFastTest(unittest.TestCase):
    def agent(self, code):
        class Boom:
            def chat(self, messages):
                raise urllib.error.HTTPError("u", code, "err", {}, None)

        return LLMAgent(Market(), Boom())

    def test_4xx_propagates_but_429_and_5xx_fall_back(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.agent(400).act(0)
        for code in (429, 500):
            self.assertTrue(self.agent(code).act(0)["fallback"])

    def test_fallback_rate_guard(self):
        out = Path(tempfile.mkdtemp())
        pf.run_case("B", 1, 6, ts.llm_factory(*[self.agent(500).client] * 2), str(out / "B_seed1.jsonl"), {})
        jobs = [("B", 1)]
        with self.assertRaisesRegex(SystemExit, "fallback"):
            ts.check_fallbacks(out, jobs, SimpleNamespace(calls=5), mock=False)
        with self.assertRaisesRegex(SystemExit, "no paid calls"):
            ts.check_fallbacks(out, jobs, SimpleNamespace(calls=0), mock=False)

    def test_mock_run_unaffected(self):
        out = Path(tempfile.mkdtemp())
        pf.run_case("B", 1, 6, ts.mock_factory, str(out / "B_seed1.jsonl"), {})
        ts.check_fallbacks(out, [("B", 1)], SimpleNamespace(calls=0), mock=True)
