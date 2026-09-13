"""Train a film recommender on MovieLens ratings (matrix factorisation).

Every user and every film gets a short vector of numbers. A user's predicted
rating for a film is the dot product of the two vectors plus a bias for each.
Training nudges the vectors until predictions match the ratings people gave;
the ratings held back measure how well it generalises. Each step is a large
batch of embedding lookups and multiplications, which is what a GPU is for.

    python movielens_recommender.py --epochs 0                 # download the data and exit
    python movielens_recommender.py                            # train on a GPU if one is visible
    python movielens_recommender.py --dim 128 --epochs 10      # bigger model, longer run
    python movielens_recommender.py --limit 100000             # first 100k ratings, fine on a CPU

Its knobs map to what a job asks PBS for: epochs to walltime, --limit and
--dim to memory, --device to the hardware request. The seed fixes the split,
shuffling and initialisation.

It needs PyTorch and pandas. The data is MovieLens 32M from GroupLens
(https://grouplens.org/datasets/movielens/32m/). The two files the script
reads are downloaded once into --data-dir from a copy on Hugging Face, and
each is checked against the MD5 checksum GroupLens publishes for it, so a
damaged or altered copy is refused. The licence allows research use, not
commercial use, and asks that publications cite: F. Maxwell Harper and
Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context.
ACM TiiS 5, 4.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request

import pandas as pd
import torch
from torch import nn

MIRROR = "https://huggingface.co/datasets/nasserCha/movielens_ratings_32m/resolve/main/"
# MD5 checksums from checksums.txt inside GroupLens's own ml-32m.zip.
FILES = {
    "ratings.csv": "cf12b74f9ad4b94a011f079e26d4270a",
    "movies.csv": "0df90835c19151f9d819d0822e190797",
}


def parse_args():
    """Parse the command line and reject sizes the training loop cannot run with."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data-dir", default="data/movielens", help="where the MovieLens files live (downloaded if missing)")
    p.add_argument("--limit", type=int, default=0, help="use only the first N ratings; 0 = all 32 million (memory and runtime)")
    p.add_argument("--dim", type=int, default=64, help="length of each user and film vector (memory and compute)")
    p.add_argument("--epochs", type=int, default=5, help="passes over the training ratings (runtime)")
    p.add_argument("--batch", type=int, default=65_536, help="ratings per optimisation step (GPU memory)")
    p.add_argument("--lr", type=float, default=0.005, help="learning rate")
    p.add_argument("--reg", type=float, default=0.05, help="penalty on large vectors, which stops the model memorising")
    p.add_argument("--test-fraction", type=float, default=0.1, help="share of ratings held back to measure error")
    p.add_argument("--top", type=int, default=10, help="films recommended per user")
    p.add_argument("--users", type=int, default=1000, help="users to write recommendations for (the first N)")
    p.add_argument("--min-ratings", type=int, default=1000, help="only recommend films rated at least this many times")
    p.add_argument("--threads", type=int, default=0, help="CPU threads; 0 = PBS's $NCPUS or 1")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--seed", type=int, default=0, help="controls the split, shuffling and initialisation")
    p.add_argument("--out", default="results.json", help="where the summary is written")
    p.add_argument("--recommendations", default="recommendations.csv", help="where the recommendations are written")
    args = p.parse_args()
    if args.dim < 1 or args.batch < 1 or args.top < 1 or args.users < 1:
        p.error("--dim, --batch, --top and --users must be at least 1")
    if args.epochs < 0 or args.threads < 0 or args.limit < 0:
        p.error("--epochs, --threads and --limit cannot be negative")
    if args.limit == 1:
        p.error("--limit must be 0 (all ratings) or at least 2, so both train and test get a rating")
    if not 0 < args.test_fraction < 1:
        p.error("--test-fraction must be between 0 and 1")
    if args.lr <= 0 or args.reg < 0 or args.min_ratings < 0:
        p.error("--lr must be positive, --reg and --min-ratings cannot be negative")
    return args


def md5_of(path):
    """MD5 checksum of a file, read in chunks so an 877 MB file needs little memory."""
    digest = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(data_dir):
    """Download the two MovieLens 32M files once and check them. Network work: do it on a login node."""
    folder = os.path.join(data_dir, "ml-32m")
    os.makedirs(folder, exist_ok=True)
    for name, expected in FILES.items():
        path = os.path.join(folder, name)
        if os.path.exists(path):
            continue
        partial = path + ".part"
        print(f"download  {MIRROR}{name}", flush=True)
        urllib.request.urlretrieve(MIRROR + name, partial)
        if md5_of(partial) != expected:
            os.remove(partial)
            sys.exit(f"ERROR: {name} does not match GroupLens's checksum; the download was damaged or the copy has changed")
        os.replace(partial, path)
        print(f"checked   {name}  matches GroupLens's checksum", flush=True)
    return folder


def load(folder, test_fraction, seed, limit):
    """Read the ratings (the first `limit` if set), renumber users and films from 0, and split train from test."""
    ratings = pd.read_csv(
        os.path.join(folder, "ratings.csv"),
        usecols=["userId", "movieId", "rating"],
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32"},
        nrows=limit or None,
    )
    movies = pd.read_csv(os.path.join(folder, "movies.csv"), usecols=["movieId", "title"])
    user_codes, user_ids = pd.factorize(ratings["userId"], sort=True)
    film_codes, film_ids = pd.factorize(ratings["movieId"], sort=True)
    users = torch.from_numpy(user_codes.astype("int64"))
    films = torch.from_numpy(film_codes.astype("int64"))
    scores = torch.from_numpy(ratings["rating"].to_numpy().copy())

    if len(scores) < 2:
        sys.exit("ERROR: need at least two ratings to split train from test")
    generator = torch.Generator().manual_seed(seed)
    order = torch.randperm(len(scores), generator=generator)
    n_test = min(max(int(len(scores) * test_fraction), 1), len(scores) - 1)
    test, train = order[:n_test], order[n_test:]
    split = {
        "train": (users[train], films[train], scores[train]),
        "test": (users[test], films[test], scores[test]),
    }
    titles = movies.set_index("movieId")["title"].reindex(film_ids).fillna("").tolist()
    counts = torch.bincount(films[train], minlength=len(film_ids))
    return split, user_ids, titles, counts, (users, films)


class MatrixFactorisation(nn.Module):
    """Predict a rating as user vector . film vector + user bias + film bias + global mean."""

    def __init__(self, n_users, n_films, dim, mean):
        super().__init__()
        self.user = nn.Embedding(n_users, dim)
        self.film = nn.Embedding(n_films, dim)
        self.user_bias = nn.Embedding(n_users, 1)
        self.film_bias = nn.Embedding(n_films, 1)
        self.mean = mean
        for table in (self.user, self.film):
            nn.init.normal_(table.weight, std=0.01)
        for table in (self.user_bias, self.film_bias):
            nn.init.zeros_(table.weight)

    def forward(self, users, films):
        u, f = self.user(users), self.film(films)
        prediction = (u * f).sum(dim=1) + self.user_bias(users).squeeze(1) + self.film_bias(films).squeeze(1) + self.mean
        size = (u.pow(2).sum(dim=1) + f.pow(2).sum(dim=1)).mean()  # how large this batch's vectors are
        return prediction, size


def pick_device(name):
    """Resolve --device: `auto` takes a GPU if one is visible, `cuda` insists on one."""
    if name == "cuda" or (name == "auto" and torch.cuda.is_available()):
        if not torch.cuda.is_available():
            sys.exit("ERROR: --device cuda requested but no GPU is visible (did you ask PBS for ngpus=1?)")
        return torch.device("cuda")
    return torch.device("cpu")


def peak_memory_mb():
    """Peak resident memory of this process, in MB. Linux and macOS only."""
    try:
        import resource
    except ImportError:  # Windows
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return kb / 1024 if sys.platform != "darwin" else kb / (1024 * 1024)


@torch.no_grad()
def rmse(model, users, films, scores, device, batch):
    """Root mean squared error of predictions against real ratings, clipped to the 0.5 to 5 scale."""
    total = 0.0
    for start in range(0, len(scores), batch):
        u, f, s = users[start : start + batch], films[start : start + batch], scores[start : start + batch]
        total += ((model(u, f)[0].clamp(0.5, 5.0) - s) ** 2).sum().item()
    return (total / len(scores)) ** 0.5


@torch.no_grad()
def recommend(model, rated_users, rated_films, counts, min_ratings, n_users, top, device):
    """Top films per user among the first `n_users`, skipping every film they rated and rarely rated films."""
    rare = (counts < min_ratings).to(device)
    picks = []
    for user in range(n_users):
        # All of this user's ratings, train and test alike: a held-out rating is still a film they have seen.
        seen = rated_films[rated_users == user]
        scores = model.film.weight @ model.user.weight[user] + model.film_bias.weight.squeeze(1)
        scores[rare] = float("-inf")
        scores[seen] = float("-inf")
        # Fewer eligible films than --top: return only those, never a masked one.
        count = min(top, int(torch.isfinite(scores).sum().item()))
        if count == 0:
            picks.append((user, [], []))
            continue
        best = torch.topk(scores, count)
        picks.append((user, best.indices.tolist(), (best.values + model.user_bias.weight[user] + model.mean).tolist()))
    return picks


def main():
    """Download if needed, train, report error per epoch, write recommendations and the summary."""
    args = parse_args()
    started = time.time()

    # PBS exports NCPUS inside a job; using exactly that many threads is what
    # makes the job's CPU use match its request.
    threads = args.threads or int(os.environ.get("NCPUS", "1"))
    torch.set_num_threads(threads)
    torch.manual_seed(args.seed)
    device = pick_device(args.device)
    gpu = torch.cuda.get_device_name(device) if device.type == "cuda" else None

    print(f"host      {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    print(f"device    {device}{f' ({gpu})' if gpu else ''}  threads {threads}  seed {args.seed}")
    folder = fetch(args.data_dir)
    if args.epochs == 0:
        # Fetch-only run, meant for the login node: stop before reading 32 million ratings.
        print(f"done      data ready in {folder}; nothing trained (--epochs 0)")
        return
    split, user_ids, titles, counts, rated = load(folder, args.test_fraction, args.seed, args.limit)
    # Move every rating to the device once. On a GPU this is a few hundred MB,
    # and it keeps each training step on the card instead of copying batches over.
    train_users, train_films, train_scores = (t.to(device) for t in split["train"])
    test_users, test_films, test_scores = (t.to(device) for t in split["test"])
    rated_users, rated_films = (t.to(device) for t in rated)
    print(f"data      {len(train_scores) + len(test_scores):,} ratings, {len(user_ids):,} users, {len(titles):,} films")

    model = MatrixFactorisation(len(user_ids), len(titles), args.dim, train_scores.mean().item()).to(device)
    optimiser = torch.optim.Adam(model.parameters(), lr=args.lr)

    test_rmse = None
    for epoch in range(args.epochs):
        epoch_started = time.time()
        model.train()
        order = torch.randperm(len(train_scores), device=device)
        for start in range(0, len(train_scores), args.batch):
            idx = order[start : start + args.batch]
            u, f, s = train_users[idx], train_films[idx], train_scores[idx]
            optimiser.zero_grad()
            prediction, size = model(u, f)
            error = ((prediction - s) ** 2).mean()
            loss = error + args.reg * size
            loss.backward()
            optimiser.step()
        model.eval()
        test_rmse = rmse(model, test_users, test_films, test_scores, device, args.batch)
        print(f"epoch {epoch + 1:>3}/{args.epochs}  train RMSE {error.item() ** 0.5:.4f}  test RMSE {test_rmse:.4f}  {time.time() - epoch_started:6.1f}s")

    n_users = min(args.users, len(user_ids))
    if args.epochs > 0:
        rows = []
        for user, films, predicted in recommend(model, rated_users, rated_films, counts, args.min_ratings, n_users, args.top, device):
            for rank, (film, score) in enumerate(zip(films, predicted), start=1):
                rows.append((int(user_ids[user]), rank, titles[film], round(min(max(score, 0.5), 5.0), 2)))
        pd.DataFrame(rows, columns=["userId", "rank", "title", "predicted_rating"]).to_csv(args.recommendations, index=False)
        print(f"wrote     top {args.top} films for {n_users:,} users -> {args.recommendations}")

    elapsed = time.time() - started
    summary = {
        "ratings": int(len(train_scores) + len(test_scores)),
        "dim": args.dim,
        "reg": args.reg,
        "epochs": args.epochs,
        "device": str(device),
        "gpu": gpu,
        "threads": threads,
        "seed": args.seed,
        "test_rmse": None if test_rmse is None else round(test_rmse, 4),
        "elapsed_s": round(elapsed, 1),
        "peak_rss_mb": None if peak_memory_mb() is None else round(peak_memory_mb()),
        "peak_gpu_mb": round(torch.cuda.max_memory_allocated(device) / 2**20) if gpu else None,
        "job_id": os.environ.get("PBS_JOBID"),
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"done      test RMSE {summary['test_rmse']}  in {elapsed:.1f}s  -> {args.out}")


if __name__ == "__main__":
    main()
