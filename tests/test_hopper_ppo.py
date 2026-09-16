"""Smoke test for the Hopper PPO script's command-line checks and checkpoint naming.

Runs without Stable-Baselines3: parse_args and the checkpoint helpers are
exercised on their own, and the functions that need the libraries import
them only when called. Training and resuming are validated by running the
script on Aqua, not here.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "tutorials" / "scripts" / "hopper_ppo.py"


def load_script():
    spec = importlib.util.spec_from_file_location("hopper_ppo", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class HopperScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def parse(self, *argv):
        with mock.patch.object(sys, "argv", ["hopper_ppo.py", *argv]):
            return self.script.parse_args()

    def test_defaults(self):
        args = self.parse()
        self.assertEqual((args.timesteps, args.save_every, args.checkpoints, args.env), (1_000_000, 50_000, "checkpoints", "Hopper-v5"))
        self.assertFalse(args.evaluate)

    def test_rejects_values_the_run_cannot_use(self):
        for argv in (["--timesteps", "0"], ["--save-every", "0"], ["--episodes", "0"]):
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    self.parse(*argv)

    def test_latest_checkpoint_is_the_one_with_most_steps(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(self.script.latest_checkpoint(d))
            for steps in (50_000, 250_000, 100_000):
                Path(self.script.checkpoint_path(d, steps)).touch()
            Path(d, "hopper_300000_steps.zip.partial").touch()
            self.assertEqual(self.script.latest_checkpoint(d), self.script.checkpoint_path(d, 250_000))


if __name__ == "__main__":
    unittest.main()
