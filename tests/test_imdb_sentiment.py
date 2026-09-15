"""Smoke test for the IMDb sentiment script's command line.

Runs without PyTorch or the Hugging Face libraries: stub modules stand in for
them so the script can be imported, and only parse_args is exercised. Training
itself is validated by running the script on Aqua, not here.
"""

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "tutorials" / "scripts" / "imdb_sentiment.py"


def load_script():
    def module(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        return m

    stubs = {
        "evaluate": module("evaluate"),
        "numpy": module("numpy"),
        "torch": module("torch"),
        "datasets": module("datasets", disable_progress_bars=None, load_dataset=None),
        "transformers": module(
            "transformers",
            AutoModelForSequenceClassification=None,
            AutoTokenizer=None,
            DataCollatorWithPadding=None,
            Trainer=None,
            TrainingArguments=None,
            pipeline=None,
            set_seed=None,
            logging=None,
        ),
    }
    with mock.patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("imdb_sentiment", SCRIPT)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
    return loaded


class ParseArgsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def parse(self, *argv):
        with mock.patch.object(sys, "argv", ["imdb_sentiment.py", *argv]):
            return self.script.parse_args()

    def test_defaults_are_the_guides(self):
        args = self.parse()
        self.assertEqual((args.epochs, args.batch, args.lr), (2, 16, 2e-5))
        self.assertEqual(args.limit, 0)
        self.assertFalse(args.fetch_only)
        self.assertEqual(args.out, "results.json")

    def test_fetch_only_is_a_flag(self):
        self.assertTrue(self.parse("--fetch-only").fetch_only)

    def test_limit_is_accepted(self):
        self.assertEqual(self.parse("--limit", "500").limit, 500)

    def test_rejects_values_training_cannot_run_with(self):
        bad = (["--limit", "-1"], ["--epochs", "0"], ["--batch", "0"], ["--lr", "0"])
        for argv in bad:
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    self.parse(*argv)

    def test_model_and_dataset_are_the_guides(self):
        self.assertEqual(self.script.MODEL, "distilbert/distilbert-base-uncased")
        self.assertEqual(self.script.DATASET, "stanfordnlp/imdb")


class OfflineModeTest(unittest.TestCase):
    """A job reads the cache without going online; only --fetch-only downloads."""

    NAMES = ("HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE", "HF_EVALUATE_OFFLINE")

    def environment_after_import(self, *argv, start=None):
        with mock.patch.dict(os.environ, start or {}, clear=True), mock.patch.object(sys, "argv", ["imdb_sentiment.py", *argv]):
            load_script()
            return dict(os.environ)

    def test_a_job_reads_the_cache_offline(self):
        env = self.environment_after_import("--epochs", "3")
        for name in self.NAMES:
            self.assertEqual(env.get(name), "1", name)

    def test_an_inherited_zero_does_not_turn_offline_mode_off(self):
        env = self.environment_after_import(start={name: "0" for name in self.NAMES})
        for name in self.NAMES:
            self.assertEqual(env.get(name), "1", name)

    def test_fetch_only_stays_online(self):
        env = self.environment_after_import("--fetch-only")
        for name in self.NAMES:
            self.assertEqual(env.get(name), "0", name)

    def test_an_inherited_one_does_not_stop_fetch_only_downloading(self):
        env = self.environment_after_import("--fetch-only", start={name: "1" for name in self.NAMES})
        for name in self.NAMES:
            self.assertEqual(env.get(name), "0", name)


if __name__ == "__main__":
    unittest.main()
