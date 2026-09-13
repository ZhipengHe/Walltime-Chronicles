"""Fine-tune DistilBERT to tell positive IMDb movie reviews from negative ones.

This is Hugging Face's own text-classification guide, turned into a script a
batch job can run: https://huggingface.co/docs/transformers/tasks/sequence_classification
The model, dataset, preprocessing, metric and training settings are the
guide's. The only changes are the ones a batch job needs: nothing is pushed to
the Hugging Face Hub, progress bars are off so the log stays readable, and the
results are written to files.

    python imdb_sentiment.py --fetch-only    # download the model and data, then exit (login node)
    python imdb_sentiment.py                 # fine-tune on the GPU PBS gave you
    python imdb_sentiment.py --limit 500     # 500 reviews each way, enough to try it on a CPU

It needs PyTorch, transformers, datasets, evaluate, accelerate and
scikit-learn. The model and data are cached under ~/.cache/huggingface.

References
    DistilBERT: V. Sanh, L. Debut, J. Chaumond and T. Wolf. 2019. DistilBERT, a
        distilled version of BERT: smaller, faster, cheaper and lighter.
        5th Workshop on Energy Efficient Machine Learning and Cognitive
        Computing, NeurIPS 2019. https://arxiv.org/abs/1910.01108
    IMDb: A. L. Maas, R. E. Daly, P. T. Pham, D. Huang, A. Y. Ng and C. Potts.
        2011. Learning Word Vectors for Sentiment Analysis. In Proceedings of
        ACL-HLT 2011, pp. 142-150.
"""

import argparse
import json
import os
import sys
import time

import evaluate
import numpy as np
import torch
from datasets import disable_progress_bars, load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    pipeline,
    set_seed,
)
from transformers import logging as transformers_logging

MODEL = "distilbert/distilbert-base-uncased"
DATASET = "stanfordnlp/imdb"
ID2LABEL = {0: "NEGATIVE", 1: "POSITIVE"}
LABEL2ID = {"NEGATIVE": 0, "POSITIVE": 1}
EXAMPLES = [
    "This was a masterpiece. Not completely faithful to the books, but enthralling from beginning to end.",
    "Two hours of my life I will never get back. The plot made no sense and the acting was wooden.",
]


def parse_args():
    """Parse the command line and reject values training cannot run with."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--fetch-only", action="store_true", help="download the model, data and metric, then exit (for the login node)")
    p.add_argument("--limit", type=int, default=0, help="use only N reviews from each split; 0 = all 25,000 (runtime)")
    p.add_argument("--epochs", type=int, default=2, help="passes over the training reviews (the guide's 2; runtime)")
    p.add_argument("--batch", type=int, default=16, help="reviews per step (the guide's 16; GPU memory)")
    p.add_argument("--lr", type=float, default=2e-5, help="learning rate (the guide's 2e-5)")
    p.add_argument("--seed", type=int, default=42, help="controls shuffling and the new classifier layer")
    p.add_argument("--model-dir", default="imdb_model", help="where checkpoints and the fine-tuned model are saved")
    p.add_argument("--out", default="results.json", help="where the summary is written")
    args = p.parse_args()
    if args.limit < 0 or args.epochs < 1 or args.batch < 1 or args.lr <= 0:
        p.error("--limit cannot be negative; --epochs and --batch must be at least 1; --lr must be positive")
    return args


def peak_memory_mb():
    """Peak resident memory of this process, in MB. Linux and macOS only."""
    try:
        import resource
    except ImportError:  # Windows
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return kb / 1024 if sys.platform != "darwin" else kb / (1024 * 1024)


def main():
    """Fetch, or fine-tune, evaluate, save the model and classify two example reviews."""
    args = parse_args()
    started = time.time()
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    print(f"host      {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    print(f"device    {'cuda (' + gpu + ')' if gpu else 'cpu'}", flush=True)

    # A batch log is read later, top to bottom: no progress bars, no library chatter.
    disable_progress_bars()
    transformers_logging.set_verbosity_error()
    transformers_logging.disable_progress_bar()

    # Seed before the model loads: its new classifier layer starts from random weights.
    set_seed(args.seed)

    # Everything below downloads on first use and is read from the cache after that.
    imdb = load_dataset(DATASET)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2, id2label=ID2LABEL, label2id=LABEL2ID)
    accuracy = evaluate.load("accuracy")
    if args.fetch_only:
        print(f"done      {MODEL} and {DATASET} are cached; nothing trained (--fetch-only)")
        return

    del imdb["unsupervised"]  # 50,000 unlabelled reviews this task never reads
    if args.limit:
        imdb["train"] = imdb["train"].shuffle(seed=args.seed).select(range(min(args.limit, len(imdb["train"]))))
        imdb["test"] = imdb["test"].shuffle(seed=args.seed).select(range(min(args.limit, len(imdb["test"]))))
    print(f"data      {len(imdb['train']):,} training reviews, {len(imdb['test']):,} test reviews", flush=True)

    # The guide's preprocessing: cut each review to DistilBERT's maximum length, pad per batch.
    tokenized = imdb.map(lambda batch: tokenizer(batch["text"], truncation=True), batched=True)

    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        return accuracy.compute(predictions=np.argmax(predictions, axis=1), references=labels)

    training_args = TrainingArguments(
        output_dir=args.model_dir,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        push_to_hub=False,  # the guide uploads; a batch job should not
        disable_tqdm=True,  # progress bars turn a log file into noise
        logging_strategy="epoch",
        report_to="none",
        seed=args.seed,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    final = trainer.evaluate()
    trainer.save_model(args.model_dir)
    print(f"accuracy  {final['eval_accuracy']:.4f} on {len(imdb['test']):,} test reviews", flush=True)

    classifier = pipeline("sentiment-analysis", model=args.model_dir, device=0 if gpu else -1)
    verdicts = classifier(EXAMPLES)
    for text, verdict in zip(EXAMPLES, verdicts):
        print(f"example   {verdict['label']:<8} {verdict['score']:.3f}  {text[:60]}...")

    elapsed = time.time() - started
    summary = {
        "model": MODEL,
        "train_reviews": len(imdb["train"]),
        "test_reviews": len(imdb["test"]),
        "epochs": args.epochs,
        "device": "cuda" if gpu else "cpu",
        "gpu": gpu,
        "accuracy": round(final["eval_accuracy"], 4),
        "examples": [{"text": t, "label": v["label"], "score": round(v["score"], 4)} for t, v in zip(EXAMPLES, verdicts)],
        "elapsed_s": round(elapsed, 1),
        "peak_rss_mb": None if peak_memory_mb() is None else round(peak_memory_mb()),
        "peak_gpu_mb": round(torch.cuda.max_memory_allocated() / 2**20) if gpu else None,
        "job_id": os.environ.get("PBS_JOBID"),
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"done      accuracy {summary['accuracy']}  in {elapsed:.1f}s  -> {args.out}, model in {args.model_dir}/")


if __name__ == "__main__":
    main()
