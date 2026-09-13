"""Smoke test for the IMDb sentiment script's command line.

Runs without PyTorch or the Hugging Face libraries: stub modules stand in for
them so the script can be imported, and only parse_args is exercised. Training
itself is validated by running the script on Aqua, not here.
"""

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
