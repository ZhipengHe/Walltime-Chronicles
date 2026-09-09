"""Smoke test for the MNIST training script's command-line checks.

Runs without PyTorch: a stub module stands in for torch so the script can be
imported, and only parse_args is exercised. Training itself is validated by
running the script on Aqua, not here.
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "tutorials" / "scripts" / "train_mnist.py"


def load_script():
    torch = types.ModuleType("torch")
    torch.no_grad = lambda: (lambda f: f)
    torch.nn = types.ModuleType("torch.nn")
    with mock.patch.dict(sys.modules, {"torch": torch, "torch.nn": torch.nn}):
        spec = importlib.util.spec_from_file_location("train_mnist", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class ParseArgsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def parse(self, *argv):
        with mock.patch.object(sys, "argv", ["train_mnist.py", *argv]):
            return self.script.parse_args()

    def test_defaults_are_accepted(self):
        args = self.parse()
        self.assertEqual(args.samples, 60_000)
        self.assertEqual(args.epochs, 8)
        self.assertEqual(args.out, "results.json")

    def test_epochs_zero_is_the_fetch_only_run(self):
        self.assertEqual(self.parse("--epochs", "0").epochs, 0)

    def test_rejects_sizes_the_training_loop_cannot_run_with(self):
        bad = (
            ["--samples", "0"],
            ["--samples", "60001"],
            ["--width", "0"],
            ["--batch", "0"],
            ["--epochs", "-1"],
            ["--threads", "-1"],
        )
        for argv in bad:
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    self.parse(*argv)


if __name__ == "__main__":
    unittest.main()
