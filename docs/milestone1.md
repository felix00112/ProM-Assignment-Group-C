# Event Log Pollution — Milestone 1

## Project Structure

```
ProM-Assignment-Group-C/
├── data/
│   ├── BPI Challenge 2017.xes.gz        ← original clean log
│   ├── polluted_data/
│   │   ├── polluted_log.xes             ← fully polluted log
│   │   └── scattered_events_validation.csv ← events removed by scattered case pattern
│   └── cleaned_data/
│       └── cleaned_log.xes              ← remediated log
├── modules/
│   ├── __init__.py
│   ├── remediation_logic.py             ← all cleaning functions
│   └── pollution_logic.py               ← all pollution functions
├── notebooks/
│   └── notebook.ipynb                   ← test notebook
└── milestone1.py                        ← main script
```

---

## Pattern 1: Synonymous Labels

### Problem
Two or more activity names are **syntactically different but semantically identical**. This commonly occurs when an event log is sourced from multiple systems or departments that use different terminology for the same step.

### Implementation
| Original | Synonym |
|---|---|
| `W_Complete application` | `W_Finish application`, `W_Finalize application` |

```python
polluted_df = add_synonymous_labels(df, fraction=0.3)
```
- Randomly selects 30% of occurrences of each target activity
- Replaces their `concept:name` with a randomly chosen synonym
- All other columns remain unchanged

### Remediation logic
The remediation step assumes that semantically similar activity labels represent the same conceptual process step. Since the injection process is unknown to the analyst, synonym detection is performed using semantic similarity of event labels (e.g., embeddings or string similarity).

The cleaning approach is:
1. Compute similarity between all unique concept:name values
2. Group labels exceeding a similarity threshold
3. Replace all variants with the most frequent label in the dataset (canonical activity)

**Constraint**: This naive approach considers only semantic similarity of activity labels and ignores the position of events in the trace as well as their predecessor and successor context, which may lead to incorrect merging of process-distinct activities.

---

## Pattern 2: Collateral Events

### Problem
Multiple recorded events all refer to the **same conceptual process step**. This happens when a workflow system automatically logs every internal state change of a work item as a separate event, even though they all belong to one logical activity.

### Injection Strategy
- `W_Complete application`: officers working on an application generates multiple rows:

```
W_Complete application | Created  | schedule   ← task queued
W_Complete application | Obtained | start      ← officer picks it up
W_Complete application | Released | suspend    ← officer pauses
W_Complete application | Obtained | resume     ← officer resumes
W_Complete application | Deleted  | complete   ← task finished
...
```
- Sub-steps are injected immediately **after** the `Obtained/start` event of `W_Complete application`, simulating fine-grained pre-checks a loan officer would perform when starting work on an application:

```
W_Complete application  | Obtained | start         ← anchor (e.g. 10:00:00)
  W_Precheck application: Applicant Identity        ← injected +1s (10:00:01)
  W_Precheck application: Form Completeness         ← injected +2s (10:00:02)
  W_Precheck application: Credit History            ← injected +3s (10:00:03)
W_Complete application  | Released | suspend        ← continues normally
```

Each injected row inherits **all column values** from the anchor event except:
- `concept:name` — updated to the sub-step name
- `time:timestamp` — incremented by 1 second per sub-step
- `start_timestamp` — same as above

### Implementation
```python
COLLATERAL_SUBSTEPS = [
    "W_Precheck application: Applicant Identity",
    "W_Precheck application: Form Completeness",
    "W_Precheck application: Credit History",
]

polluted_df = add_collateral_events(df, fraction=0.001)
```

### Remediation logic
Collateral events are identified as fine-grained sub-steps of a single logical activity, which appear in close temporal proximity within the same case. Since the injection logic is unknown, the analyst relies on:
- Temporal proximity (events occurring within seconds)
- Semantic relatedness (similar or structured naming patterns, e.g. Parent Activity: Substep)

The cleaning strategy is:
- Detect groups of events belonging to the same conceptual activity (via dictionary or similarity + prefix patterns)
- Within each case, identify the earliest occurrence of the group
- Merge all sub-events into a single canonical activity
- Remove redundant sub-events while preserving process order

**Problem**: Without knowledge of the underlying injection logic, a downstream analyst may incorrectly interpret the injected collateral sub-steps as a genuinely new high-level activity (e.g., "W_Precheck application"). While the original intent was to remove fine-grained sub-events of "W_Complete application", the analyst only observes fragmented and semantically related labels, leading to the unintended creation of a new activity that does not exist in the true business process.

---

## Pattern 3: Scattered Cases

### Problem
Key events belonging to a case are **missing from the main event log** because they were recorded in a separate system. The case exists but is incomplete, creating visible gaps in the process model.

### Implementation
The equivalent in the loan process is removing all **validation-related events**, simulating that they were recorded in a separate compliance system:

```python
polluted_df = add_scattered_cases(
    df,
    output_path="data/polluted_data/scattered_events_validation.csv",
    concept_name="valid"   # matches W_Validate application and A_Validating
)
```
- Removes all events whose `concept:name` contains `"valid"` (case-insensitive)
- Saves removed events to a CSV (the simulated "other system")
- Returns the remaining log with gaps