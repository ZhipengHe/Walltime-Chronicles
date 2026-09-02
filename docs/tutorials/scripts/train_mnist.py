"""Train a small network to recognise handwritten digits (MNIST).

The Crash Course's one worked example. Lesson 3 runs it by hand and measures
it; every later lesson turns one of its knobs: more epochs (walltime), more
samples or a wider layer (memory), more threads or a GPU (right-sizing), a
seed per job (arrays), and a checkpoint file (long jobs).

    python train_mnist.py                        # ~half a minute on one core
    python train_mnist.py --epochs 20            # longer
    python train_mnist.py --width 4096           # heavier on memory and compute
    python train_mnist.py --device cuda          # use the GPU PBS gave you
    python train_mnist.py --seed 7 --out run7.json
    python train_mnist.py --checkpoint ckpt.pt   # resumes if the file exists

It needs only PyTorch. The data (60,000 training and 10,000 test images,
about 12 MB compressed) is downloaded once into --data-dir and read straight
from the original IDX files; no torchvision, no numpy.
"""

import argparse
import gzip
import json
import os
import sys
import time
import urllib.request

import torch
from torch import nn

MIRROR = "https://ossci-datasets.s3.amazonaws.com/mnist/"
FILES = {
    "train_images": "train-images-idx3-ubyte.gz",
    "train_labels": "train-labels-idx1-ubyte.gz",
    "test_images": "t10k-images-idx3-ubyte.gz",
    "test_labels": "t10k-labels-idx1-ubyte.gz",
}


def parse_args():
    """Parse the command line and reject sizes the training loop cannot run with."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data-dir", default="data/mnist", help="where the four MNIST files live (downloaded if missing)")
    p.add_argument("--samples", type=int, default=60_000, help="training images to use, up to 60,000 (memory)")
    p.add_argument("--width", type=int, default=1024, help="hidden layer width (memory and compute per step)")
    p.add_argument("--epochs", type=int, default=8, help="passes over the data (runtime)")
    p.add_argument("--batch", type=int, default=128, help="images per optimisation step")
    p.add_argument("--threads", type=int, default=0, help="CPU threads; 0 = PBS's $NCPUS or 1")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--seed", type=int, default=0, help="controls shuffling and initialisation")
    p.add_argument("--checkpoint", default=None, help="path to save after each epoch and resume from")
    p.add_argument("--out", default="results.json", help="where the summary is written")
    args = p.parse_args()
    if not 1 <= args.samples <= 60_000:
        p.error("--samples must be between 1 and 60000")
    if args.width < 1 or args.batch < 1:
        p.error("--width and --batch must be at least 1")
    if args.epochs < 0 or args.threads < 0:
        p.error("--epochs and --threads cannot be negative")
    return args


def fetch(data_dir):
    """Download the four MNIST files once. Network work: do it on a login node."""
    os.makedirs(data_dir, exist_ok=True)
    for name in FILES.values():
        path = os.path.join(data_dir, name)
        if not os.path.exists(path):
            print(f"download  {MIRROR}{name}")
            urllib.request.urlretrieve(MIRROR + name, path)


def read_idx(path):
    """Read one IDX file (the original MNIST format) into a uint8 tensor."""
    with gzip.open(path, "rb") as f:
        data = f.read()
    ndim = data[3]  # third byte of the magic number: 1 for labels, 3 for images
    header = 4 + 4 * ndim
    shape = [int.from_bytes(data[4 + 4 * i : 8 + 4 * i], "big") for i in range(ndim)]
    return torch.frombuffer(bytearray(data[header:]), dtype=torch.uint8).view(*shape)


def load(data_dir, samples, device):
    """Return train and test tensors on `device`, using the first `samples` training images."""
    fetch(data_dir)
    x_train = read_idx(os.path.join(data_dir, FILES["train_images"]))[:samples]
    y_train = read_idx(os.path.join(data_dir, FILES["train_labels"]))[:samples]
    x_test = read_idx(os.path.join(data_dir, FILES["test_images"]))
    y_test = read_idx(os.path.join(data_dir, FILES["test_labels"]))
    # Pixels to floats in [0, 1], flattened to 784 per image. This conversion
    # is where the memory goes: 60,000 x 784 x 4 bytes is about 188 MB.
    to_float = lambda t: t.reshape(t.shape[0], -1).float().div_(255).to(device)
    return to_float(x_train), y_train.long().to(device), to_float(x_test), y_test.long().to(device)


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
def accuracy(model, x, y, batch=1000):
    """Fraction of `x` classified correctly, evaluated in batches to bound memory."""
    correct = 0
    for start in range(0, x.shape[0], batch):
        correct += (model(x[start : start + batch]).argmax(1) == y[start : start + batch]).sum().item()
    return correct / x.shape[0]


def main():
    """Train, report per-epoch accuracy, and write the JSON summary."""
    args = parse_args()
    started = time.time()

    # PBS exports NCPUS inside a job; using exactly that many threads is what
    # makes the job's cpupercent match its request.
    threads = args.threads or int(os.environ.get("NCPUS", "1"))
    torch.set_num_threads(threads)
    torch.manual_seed(args.seed)
    device = pick_device(args.device)

    print(f"host      {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    print(f"device    {device}  threads {threads}  seed {args.seed}")
    x_train, y_train, x_test, y_test = load(args.data_dir, args.samples, device)
    print(f"data      {x_train.shape[0]:,} training images, {x_test.shape[0]:,} test  ({x_train.numel() * 4 / 1e6:.0f} MB)")

    model = nn.Sequential(
        nn.Linear(784, args.width),
        nn.ReLU(),
        nn.Linear(args.width, 10),
    ).to(device)
    optimiser = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    # Resume if a checkpoint exists. Lesson 8 relies on this: a job that runs
    # out of walltime can be resubmitted and carries on from the last epoch.
    first_epoch = 0
    if args.checkpoint and os.path.exists(args.checkpoint):
        state = torch.load(args.checkpoint, map_location=device, weights_only=True)
        model.load_state_dict(state["model"])
        optimiser.load_state_dict(state["optimiser"])
        first_epoch = state["epoch"] + 1
        print(f"resumed   from {args.checkpoint} at epoch {first_epoch}")

    test_acc = float("nan")
    for epoch in range(first_epoch, args.epochs):
        epoch_started = time.time()
        model.train()
        order = torch.randperm(x_train.shape[0], device=device)
        for start in range(0, x_train.shape[0], args.batch):
            idx = order[start : start + args.batch]
            optimiser.zero_grad()
            loss = loss_fn(model(x_train[idx]), y_train[idx])
            loss.backward()
            optimiser.step()
        model.eval()
        test_acc = accuracy(model, x_test, y_test)
        print(f"epoch {epoch + 1:>3}/{args.epochs}  loss {loss.item():.4f}  test accuracy {test_acc:.4f}  {time.time() - epoch_started:5.1f}s")
        if args.checkpoint:
            torch.save(
                {"model": model.state_dict(), "optimiser": optimiser.state_dict(), "epoch": epoch},
                args.checkpoint,
            )

    elapsed = time.time() - started
    summary = {
        "seed": args.seed,
        "samples": int(x_train.shape[0]),
        "width": args.width,
        "epochs": args.epochs,
        "device": str(device),
        "threads": threads,
        "test_accuracy": None if test_acc != test_acc else round(test_acc, 4),  # None when no epoch ran
        "elapsed_s": round(elapsed, 1),
        "peak_rss_mb": None if peak_memory_mb() is None else round(peak_memory_mb()),
        "job_id": os.environ.get("PBS_JOBID"),
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"done      test accuracy {summary['test_accuracy']}  in {elapsed:.1f}s  -> {args.out}")


if __name__ == "__main__":
    main()
