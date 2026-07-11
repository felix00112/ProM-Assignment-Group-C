# ProM Assignment Group C

## Milestone 1 Documentation

This project simulates and resolves common data quality issues in event logs using process mining techniques on the **BPI Challenge 2017 dataset**.

Execute the **pollution script** by running:

```text
milestone1/polluter-script.ipynb
```

Execute the **cleaning script** by running:
```text
milestone1/cleaning-script.ipynb
```

The three resulting **datasets** can be found here:
```text
data/BPI Challenge 217.xes.gz     # clean log
data/noised.xes.gz
data/recovered.xes.gz
```
In order to run the cleaning script correctly you need to run it within a GitHub Codespace (Secret API Key is needed, which is stored as a secret  in the repo).

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/felix00112/ProM-Assignment-Group-C)

How to use codespaces: https://docs.github.com/en/codespaces/developing-in-a-codespace/developing-in-a-codespace

## Milestone 2 Documentation

This Milestone applies 3 discovery algorithms on the **BPI Challenge 2017 dataset**.

Relevant jupyter notebooks can be found here:

```text
milestone2/alpha-algorithm-new.ipynb
milestone2/heuristic_miner.ipynb
milestone2/inductive_miner.ipynb
```

Graph outputs are stored here:
```text
data/milestone2/
```

## Milestone 3 Documentation

This Milestone applies two complementary conformance checking techniques —
**token-based replay** and **alignment-based conformance** — to compare each
of the three M1 logs against the reference model from M2.

Relevant notebooks can be found here:

```text
milestone3/token_based_replay_fitness.ipynb   # Task 1: token-based replay
milestone3/alignment_based.ipynb              # Task 2: alignment-based conformance
```

### Task 1 — Token-Based Replay

Aggregates to log-level fitness and perfect-case ratio,
and identifies the top-5 conformance hotspot places per log.
Per-variant output tables are stored here:
```text
data/milestone3/tbr_per_variant_fitness_clean.csv
data/milestone3/tbr_per_variant_fitness_noised.csv
data/milestone3/tbr_per_variant_fitness_recovered.csv
```
### Task 2 — Alignment-Based Conformance

Reports absolute and normalised fitness per log, and
identifies the top-5 hotspot activities by model-move and log-move counts.
Per-variant output tables are stored here:
```text
data/milestone3/alignment_per_variant_clean.csv
data/milestone3/alignment_per_variant_noised.csv
data/milestone3/alignment_per_variant_recovered.csv
```

Aggregate fitness and hotspot tables are stored here:
```text
data/milestone3/task2b_aggregate_fitness.csv
data/milestone3/task2c_hotspots_clean.csv
data/milestone3/task2c_hotspots_noised.csv
data/milestone3/task2c_hotspots_recovered.csv
```

---

## Milestone 4 Documentation

This Milestone enhances the reference model in two ways: extending it with
**performance information** (waiting and processing times) and **repairing**
its control flow.

Relevant notebooks can be found here:

```text
milestone4/performance_enhancement.ipynb
```

### Task 1a — Performance Annotation

Calculates the average waiting time before each activity and the average processing time of each activity for the clean, noised, and recovered event logs. The resulting timing statistics are used to identify process bottlenecks and compare the impact of noise and recovery on performance analysis.

Per-activity timing tables are stored here:
```text
data/milestone4/timing_clean.csv
data/milestone4/timing_noised.csv
data/milestone4/timing_recovered.csv
```

### Task 1b — Model Repair

Evaluates the discovered Petri net using token-based replay fitness and precision, then performs a simple repair by removing a selected silent (tau) transition. The repaired model is re-evaluated to measure the effect of the modification on model quality.

---

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/felix00112/ProM-Assignment-Group-C
cd ProM-Assignment-Group-C
````

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start Jupyter Notebook:

```bash
jupyter notebook
```

5. Open the milestone related notebooks:

```text
notebooks/notebook.ipynb
```
### Useful Hints

The dataset is located in:

```text
data/BPI Challenge 2017.xes.gz
```

The event log can be loaded with:

```python
import pm4py

log = pm4py.read_xes("../data/BPI Challenge 2017.xes.gz")
df = pm4py.convert_to_dataframe(log)

df.head()
```

For PM4Py visualizations, Graphviz may be required:

```bash
brew install graphviz
```
