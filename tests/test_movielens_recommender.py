"""Smoke test for the MovieLens recommender script's command line and download check.

Runs without PyTorch or pandas: stub modules stand in for both so the script
can be imported. Only argument parsing and the checksum-checked download are
exercised, with the network replaced by a local fake. Training itself is
validated by running the script on Aqua, not here.
"""

import hashlib
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "tutorials" / "scripts" / "movielens_recommender.py"


def load_script():
    torch = types.ModuleType("torch")
    torch.no_grad = lambda: (lambda f: f)
    torch.nn = types.ModuleType("torch.nn")
    torch.nn.Module = object
    pandas = types.ModuleType("pandas")
    stubs = {"torch": torch, "torch.nn": torch.nn, "pandas": pandas}
    with mock.patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("movielens_recommender", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class ParseArgsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def parse(self, *argv):
        with mock.patch.object(sys, "argv", ["movielens_recommender.py", *argv]):
            return self.script.parse_args()

    def test_defaults_are_accepted(self):
        args = self.parse()
        self.assertEqual(args.limit, 0)
        self.assertEqual(args.top, 10)
        self.assertEqual(args.out, "results.json")
        self.assertEqual(args.recommendations, "recommendations.csv")

    def test_epochs_zero_is_the_fetch_only_run(self):
        self.assertEqual(self.parse("--epochs", "0").epochs, 0)

    def test_limit_is_accepted(self):
        self.assertEqual(self.parse("--limit", "100000").limit, 100000)

    def test_rejects_values_the_training_loop_cannot_run_with(self):
        bad = (
            ["--dim", "0"],
            ["--batch", "0"],
            ["--top", "0"],
            ["--users", "0"],
            ["--epochs", "-1"],
            ["--threads", "-1"],
            ["--limit", "-1"],
            ["--test-fraction", "0"],
            ["--test-fraction", "1"],
            ["--lr", "0"],
            ["--reg", "-0.1"],
            ["--min-ratings", "-1"],
        )
        for argv in bad:
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    self.parse(*argv)


class FetchTest(unittest.TestCase):
    """The download keeps files that match GroupLens's checksums and refuses the rest."""

    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def fake_download(self, contents):
        def urlretrieve(url, path):
            with open(path, "wb") as f:
                f.write(contents[url.rsplit("/", 1)[1]])
        return urlretrieve

    def test_matching_files_are_kept(self):
        contents = {"ratings.csv": b"good ratings", "movies.csv": b"good movies"}
        checksums = {name: hashlib.md5(data).hexdigest() for name, data in contents.items()}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(self.script, "FILES", checksums), \
                mock.patch.object(self.script.urllib.request, "urlretrieve", self.fake_download(contents)), \
                mock.patch("sys.stdout"):
            folder = self.script.fetch(tmp)
            self.assertEqual(sorted(os.listdir(folder)), ["movies.csv", "ratings.csv"])

    def test_a_mismatched_file_is_refused_and_removed(self):
        contents = {"ratings.csv": b"tampered ratings", "movies.csv": b"good movies"}
        checksums = {"ratings.csv": hashlib.md5(b"good ratings").hexdigest(),
                     "movies.csv": hashlib.md5(b"good movies").hexdigest()}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(self.script, "FILES", checksums), \
                mock.patch.object(self.script.urllib.request, "urlretrieve", self.fake_download(contents)), \
                mock.patch("sys.stdout"):
            with self.assertRaises(SystemExit):
                self.script.fetch(tmp)
            self.assertEqual(os.listdir(os.path.join(tmp, "ml-32m")), [])

    def test_the_published_checksums_are_the_ones_grouplens_ships(self):
        self.assertEqual(self.script.FILES["ratings.csv"], "cf12b74f9ad4b94a011f079e26d4270a")
        self.assertEqual(self.script.FILES["movies.csv"], "0df90835c19151f9d819d0822e190797")


if __name__ == "__main__":
    unittest.main()
