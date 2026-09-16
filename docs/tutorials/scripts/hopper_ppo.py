"""Teach a MuJoCo Hopper to hop with PPO, saving as it goes, and resume if stopped.

The task is Gymnasium's Hopper: a one-legged robot rewarded for moving
forward without falling. The learner is PPO from Stable-Baselines3, with
its default settings. Every --save-every environment steps the whole model
is saved into checkpoints/, as Stable-Baselines3's CheckpointCallback does,
except that each file is written into place only once it is complete. When
the script starts and a checkpoint exists, training continues from it, so a
run that was stopped picks up where it left off.

    python hopper_ppo.py --timesteps 1000000        # train; resume from checkpoints/ if any
    python hopper_ppo.py --evaluate                 # run the latest policy -> results.json
    python hopper_ppo.py --timesteps 4096 --checkpoints test_ckpt   # a short check

It needs stable-baselines3 and gymnasium[mujoco]. Nothing is downloaded.
"""

import argparse
import glob
import json
import os
import re
import sys
import time


def parse_args():
    """Parse the command line and reject values the run cannot use."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--timesteps", type=int, default=1_000_000, help="environment steps to train in total, across restarts")
    p.add_argument("--save-every", type=int, default=50_000, help="environment steps between checkpoints")
    p.add_argument("--checkpoints", default="checkpoints", help="where checkpoints are written and resumed from")
    p.add_argument("--env", default="Hopper-v5", help="the Gymnasium environment")
    p.add_argument("--seed", type=int, default=0, help="seed for the environment and the learner")
    p.add_argument("--evaluate", action="store_true", help="run the latest checkpoint's policy, then exit")
    p.add_argument("--episodes", type=int, default=10, help="episodes to run with --evaluate")
    p.add_argument("--out", default="results.json", help="where --evaluate writes its result")
    args = p.parse_args()
    if args.timesteps < 1 or args.save_every < 1 or args.episodes < 1:
        p.error("--timesteps, --save-every and --episodes must all be at least 1")
    return args


def peak_memory_mb():
    """Peak resident memory of this process, in MB. Linux and macOS only."""
    try:
        import resource
    except ImportError:  # Windows
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return kb / 1024 if sys.platform != "darwin" else kb / (1024 * 1024)


def checkpoint_path(directory, steps):
    """checkpoints/hopper_250000_steps.zip, the naming CheckpointCallback uses."""
    return os.path.join(directory, f"hopper_{steps}_steps.zip")


def latest_checkpoint(directory):
    """The checkpoint with the most steps, or None."""
    found = []
    for path in glob.glob(checkpoint_path(directory, "*")):
        match = re.search(r"hopper_(\d+)_steps\.zip$", path)
        if match:
            found.append((int(match.group(1)), path))
    return max(found)[1] if found else None


def make_saver(directory, save_every):
    """A callback that saves the model every save_every environment steps, written into place when complete."""
    from stable_baselines3.common.callbacks import BaseCallback

    class SaveEvery(BaseCallback):
        def __init__(self):
            super().__init__()
            self.last_saved = None
            self.started = time.time()

        def save(self):
            path = checkpoint_path(directory, self.model.num_timesteps)
            self.model.save(path + ".partial")
            os.replace(path + ".partial", path)
            self.last_saved = self.model.num_timesteps
            rewards = [info["r"] for info in self.model.ep_info_buffer]
            mean = sum(rewards) / len(rewards) if rewards else float("nan")
            print(f"saved     {self.model.num_timesteps:>9,} steps  mean reward {mean:7.1f}  at {time.time() - self.started:.0f}s  -> {path}", flush=True)

        def _on_training_start(self):
            self.last_saved = self.model.num_timesteps

        def _on_step(self):
            if self.model.num_timesteps - self.last_saved >= save_every:
                self.save()
            return True

    return SaveEvery()


def train(args):
    """Train up to --timesteps environment steps, continuing from the latest checkpoint if there is one."""
    import gymnasium as gym
    import torch
    from stable_baselines3 import PPO

    torch.set_num_threads(int(os.environ.get("NCPUS", os.cpu_count() or 1)))
    env = gym.make(args.env)
    latest = latest_checkpoint(args.checkpoints)
    if latest:
        model = PPO.load(latest, env=env)
        print(f"resume    from {latest}: {model.num_timesteps:,} of {args.timesteps:,} steps done")
    else:
        os.makedirs(args.checkpoints, exist_ok=True)
        model = PPO("MlpPolicy", env, seed=args.seed, verbose=0)
        print(f"start     no checkpoint in {args.checkpoints}/; training from scratch")

    remaining = args.timesteps - model.num_timesteps
    if remaining <= 0:
        print(f"done      all {args.timesteps:,} steps were already trained; nothing to do")
        return

    saver = make_saver(args.checkpoints, args.save_every)
    started = time.time()
    model.learn(total_timesteps=remaining, callback=saver, reset_num_timesteps=False)
    if saver.last_saved != model.num_timesteps:
        saver.save()
    peak = peak_memory_mb()
    print(f"done      {model.num_timesteps:,} steps trained in {time.time() - started:.0f}s" + (f", peak memory {peak:.0f} MB" if peak else ""))


def evaluate(args):
    """Run the latest checkpoint's policy for --episodes episodes and write the mean reward."""
    import gymnasium as gym
    from stable_baselines3 import PPO
    from stable_baselines3.common.evaluation import evaluate_policy

    latest = latest_checkpoint(args.checkpoints)
    if not latest:
        sys.exit(f"no checkpoint in {args.checkpoints}/ to evaluate")
    env = gym.make(args.env)
    model = PPO.load(latest, env=env)
    mean, std = evaluate_policy(model, env, n_eval_episodes=args.episodes)
    print(f"policy    {latest} ({model.num_timesteps:,} steps)")
    print(f"reward    {mean:.1f} +/- {std:.1f} over {args.episodes} episodes")

    result = {
        "env": args.env,
        "timesteps": model.num_timesteps,
        "checkpoint": latest,
        "episodes": args.episodes,
        "mean_reward": round(float(mean), 1),
        "std_reward": round(float(std), 1),
        "job_id": os.environ.get("PBS_JOBID"),
    }
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"done      mean reward {mean:.1f} -> {args.out}")


def main():
    """Train or evaluate, as asked."""
    args = parse_args()
    print(f"host      {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}  job {os.environ.get('PBS_JOBID', '-')}")
    print(f"env       {args.env}  seed {args.seed}")

    if args.evaluate:
        evaluate(args)
        return
    train(args)


if __name__ == "__main__":
    main()
