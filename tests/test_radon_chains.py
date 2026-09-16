"""Smoke test for the radon chain script's command-line checks.

Runs without PyMC: parse_args is exercised on its own, and the model-building
functions import their libraries only when called. Sampling itself is
validated by running the script on Aqua, not here.
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "tutorials" / "scripts" / "radon_chains.py"


def load_script():
    spec = importlib.util.spec_from_file_location("radon_chains", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class ParseArgsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def parse(self, *argv):
        with mock.patch.object(sys, "argv", ["radon_chains.py", *argv]):
            return self.script.parse_args()

    def test_defaults(self):
        args = self.parse()
        self.assertEqual((args.seed, args.draws, args.tune), (0, 4000, 2000))
        self.assertEqual(args.out, "chain.nc")
        self.assertFalse(args.compile_only)

    def test_the_index_becomes_the_seed_and_the_file(self):
        args = self.parse("--seed", "3", "--out", "chains/chain_3.nc")
        self.assertEqual(args.seed, 3)
        self.assertEqual(args.out, "chains/chain_3.nc")

    def test_compile_only_is_a_flag(self):
        self.assertTrue(self.parse("--compile-only").compile_only)

    def test_rejects_values_the_sampler_cannot_run_with(self):
        for argv in (["--draws", "0"], ["--tune", "-1"]):
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    self.parse(*argv)


if __name__ == "__main__":
    unittest.main()
