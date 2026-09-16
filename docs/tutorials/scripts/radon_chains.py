"""Run one MCMC chain of PyMC's multilevel radon model.

The model is the varying-intercept model from PyMC's primer on multilevel
modelling, fitted to radon measurements from 919 households across 85
Minnesota counties (Gelman and Hill, 2006). The data is the primer's two
files, srrs2.dat and cty.dat, read from the working directory.

One run is one chain. Its knobs map to what a job asks PBS for: draws and
tune to walltime, the seed to which chain this is. Several chains, each from
a different seed, are combined afterwards to check that they agree.

    python radon_chains.py --compile-only              # build the model, sample nothing
    python radon_chains.py --seed 3 --out chains/chain_3.nc
    python radon_chains.py --draws 500 --tune 500       # a short chain

It needs pymc, arviz and netcdf4. The chain is written as a NetCDF file that
arviz.from_netcdf reads back, and a JSON summary is written beside it.
"""

import argparse
import json
import os
import sys
import time


def parse_args():
    """Parse the command line and reject values the sampler cannot run with."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--seed", type=int, default=0, help="the chain's seed; each chain needs its own")
    p.add_argument("--draws", type=int, default=4000, help="samples to keep after tuning (runtime)")
    p.add_argument("--tune", type=int, default=2000, help="tuning steps before the kept samples (runtime)")
    p.add_argument("--out", default="chain.nc", help="where the chain is written (NetCDF)")
    p.add_argument("--compile-only", action="store_true", help="build and compile the model, then exit")
    args = p.parse_args()
    if args.draws < 1 or args.tune < 0:
        p.error("--draws must be at least 1 and --tune cannot be negative")
    return args


def peak_memory_mb():
    """Peak resident memory of this process, in MB. Linux and macOS only."""
    try:
        import resource
    except ImportError:  # Windows
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return kb / 1024 if sys.platform != "darwin" else kb / (1024 * 1024)


def load_radon():
    """Return (log_radon, floor, county index, county names) for Minnesota, as the primer prepares them."""
    import numpy as np
    import pandas as pd

    srrs2 = pd.read_csv("srrs2.dat")
    srrs2.columns = srrs2.columns.map(str.strip)
    srrs_mn = srrs2[srrs2.state == "MN"].copy()

    cty = pd.read_csv("cty.dat")
    cty_mn = cty[cty.st == "MN"].copy()
    cty_mn["fips"] = 1000 * cty_mn.stfips + cty_mn.ctfips

    srrs_mn["fips"] = srrs_mn.stfips * 1000 + srrs_mn.cntyfips
    srrs_mn = srrs_mn.merge(cty_mn[["fips", "Uppm"]], on="fips")
    srrs_mn = srrs_mn.drop_duplicates(subset="idnum")
    srrs_mn["county"] = srrs_mn.county.map(str.strip)

    county, counties = srrs_mn.county.factorize()
    log_radon = np.log(srrs_mn.activity + 0.1).values
    floor = srrs_mn.floor.values
    return log_radon, floor, county, list(counties)


def build_model(log_radon, floor, county, counties):
    """The primer's varying-intercept model: one intercept per county, one floor effect for all."""
    import pymc as pm

    coords = {"county": counties, "obs_id": range(len(log_radon))}
    with pm.Model(coords=coords) as model:
        floor_idx = pm.Data("floor_idx", floor, dims="obs_id")
        county_idx = pm.Data("county_idx", county, dims="obs_id")

        mu_a = pm.Normal("mu_a", mu=0.0, sigma=10.0)
        sigma_a = pm.Exponential("sigma_a", 1.0)
        a = pm.Normal("a", mu=mu_a, sigma=sigma_a, dims="county")
        b = pm.Normal("b", mu=0.0, sigma=10.0)
        sigma = pm.Exponential("sigma", 1.0)

        theta = a[county_idx] + b * floor_idx
        pm.Normal("y", mu=theta, sigma=sigma, observed=log_radon, dims="obs_id")
    return model


def main():
    """Build the model, run one chain, write it and its summary."""
    args = parse_args()
    started = time.time()

    print(f"host      {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    print(f"seed      {args.seed}  draws {args.draws}  tune {args.tune}")

    import pymc as pm

    log_radon, floor, county, counties = load_radon()
    print(f"data      {len(log_radon):,} households in {len(counties)} counties")

    model = build_model(log_radon, floor, county, counties)

    # Compiling the model is what fills PyTensor's cache. --compile-only does
    # exactly that and stops, which is a cheap check that the script runs
    # before eight copies of it are queued.
    compile_started = time.time()
    with model:
        model.compile_logp()(model.initial_point())
        model.compile_dlogp()(model.initial_point())
    print(f"compiled  in {time.time() - compile_started:.1f}s")
    if args.compile_only:
        print("done      model built and compiled; nothing sampled (--compile-only)")
        return

    sample_started = time.time()
    with model:
        idata = pm.sample(
            draws=args.draws,
            tune=args.tune,
            chains=1,
            cores=1,
            random_seed=args.seed,
            progressbar=False,
        )
    sample_s = time.time() - sample_started

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    # The chain appears under its final name only once it is fully written,
    # so a job that tests for the file before redoing the run can trust it.
    partial = args.out + ".partial"
    idata.to_netcdf(partial)
    os.replace(partial, args.out)

    divergences = int(idata.sample_stats["diverging"].sum())
    elapsed = time.time() - started
    summary = {
        "seed": args.seed,
        "draws": args.draws,
        "tune": args.tune,
        "divergences": divergences,
        "sample_s": round(sample_s, 1),
        "elapsed_s": round(elapsed, 1),
        "peak_rss_mb": None if peak_memory_mb() is None else round(peak_memory_mb()),
        "job_id": os.environ.get("PBS_JOBID"),
        "array_index": os.environ.get("PBS_ARRAY_INDEX"),
    }
    summary_path = os.path.splitext(args.out)[0] + ".json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"sampled   {args.draws} draws in {sample_s:.1f}s  divergences {divergences}")
    print(f"done      chain {args.seed} in {elapsed:.1f}s  -> {args.out}, {summary_path}")


if __name__ == "__main__":
    main()
