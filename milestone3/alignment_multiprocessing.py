import time
import pm4py
import pandas as pd
import os
import csv
import json
from pathlib import Path

from pm4py.statistics.variants.log import get as variants_get
from pm4py.algo.conformance.alignments.petri_net import algorithm as aligner

import warnings
warnings.filterwarnings("ignore")

from multiprocessing import freeze_support

DATA_DIR = Path.cwd().parent / "data"
OUTPUT_DIR = DATA_DIR / "milestone3"

CASE = "recovered"

BATCH_SIZE = 32


def classify_and_cost(aligned_trace):
    cost = 0
    log_moves = []
    model_moves = []

    for l, m in aligned_trace:
        log_skip = (l == ">>")
        model_skip = (m == ">>")

        if not log_skip and not model_skip:
            if l != m:
                return float("inf"), [], []
            continue

        elif log_skip and not model_skip:
            if m is not None:
                cost += 1
                model_moves.append(m)

        elif model_skip and not log_skip:
            if l is not None:
                cost += 1
                log_moves.append(l)

    return cost, model_moves, log_moves


def main():

    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------- LOAD LOG ----------------
    if CASE == "clean":
        log = pm4py.read_xes(str(DATA_DIR / "BPI Challenge 2017.xes.gz"))
    elif CASE == "noised":
        log = pm4py.read_xes(str(DATA_DIR / "noised.xes.gz"))
    else:
        log = pm4py.read_xes(str(DATA_DIR / "recovered.xes.gz"))

    print(f"Loaded {CASE} log: {sum(len(t) for t in log)} events, {len(log)} cases")

    # ---------------- MODEL ----------------
    net_clean, im_clean, fm_clean = pm4py.read_pnml(
        f"{OUTPUT_DIR}/reference_model_clean.pnml"
    )

    # ---------------- VARIANTS ----------------
    variants = variants_get.get_variants(log)
    print(f"{len(variants)} variants")

    output_file = f"alignment_per_variant_{CASE}.csv"

    # ---------------- CHECKPOINT ----------------
    if os.path.exists(OUTPUT_DIR / output_file):
        df_existing = pd.read_csv(OUTPUT_DIR / output_file)
        done_variants = set(df_existing["variant"].astype(str))
    else:
        done_variants = set()

    remaining = [
        (v, t)
        for v, t in variants.items()
        if str(v) not in done_variants
    ]

    # ---------------- BATCH PROCESSING ----------------
    while remaining:

        batch = remaining[:BATCH_SIZE]
        remaining = remaining[BATCH_SIZE:]

        batch_traces = [t[0] for _, t in batch]
        batch_variants = [v for v, _ in batch]

        alignments = aligner.apply_multiprocessing(
            batch_traces,
            net_clean,
            im_clean,
            fm_clean
        )

        rows = []

        for variant, alignment, (_, traces) in zip(batch_variants, alignments, batch):

            aligned = alignment["alignment"]
            cost, model_moves, log_moves = classify_and_cost(aligned)

            rows.append({
                "variant": variant,
                "frequency": len(traces),
                "cost": cost,
                "alignment": json.dumps(aligned),
                "model_moves": json.dumps(model_moves),
                "log_moves": json.dumps(log_moves)
            })

            print(f"Processed variant: length={len(variant)} | cost={cost}")

        # ---------------- SAVE BATCH ----------------
        df = pd.DataFrame(rows)
        df.to_csv(
            OUTPUT_DIR / output_file,
            mode="a",
            header=not os.path.exists(OUTPUT_DIR / output_file),
            index=False
        )

        progress = (16471 - len(remaining))
        print(f"Saved batch of {len(batch)} variants, remaining: {len(remaining)}, progress: {progress}/16471")


# IMPORTANT for Windows multiprocessing
if __name__ == "__main__":
    freeze_support()
    main()