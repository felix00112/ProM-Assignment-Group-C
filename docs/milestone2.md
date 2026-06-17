# Heuristic Mining — Milestone 2

## Theoretical background
- **The Problem It Solves**: The α-Algorithm looks at every directly follows relation in the log equally. In real noisy logs this causes spaghetti models because rare, accidental sequences get the same weight as the dominant process flow. Heuristic Mining says: not all connections are equally important and frequency decides what matters.

- **The Core Idea**: Instead of asking "does A ever directly follow B?" it asks "how often does A directly follow B, and is the relationship strong enough to be causal?". It introduces two concepts:
    - **Frequency**: how often does something happen?
    - **Dependency**: how strongly does A cause B (vs B causing A)?

### Step 1: Build the Frequency Table
- For every pair of activities (a, b) in the log, count how many times a is directly followed by b across all traces. This gives you |a >L b| or |a>b|
- For example:
```
W_Complete application → W_Call after offers : 15,000 times
W_Complete application → W_Validate application : 12,000 times
W_Precheck: Identity → W_Complete application : 30 times  ← injected noise
```

### Step 2: Compute the Dependency Value
- Frequency alone isn't enough. High frequency of A → B doesn't mean A causes B — maybe B also frequently causes A (a loop). The dependency measure captures the asymmetry:
```
For a ≠ b:
dep(a→b) = (|a>b| - |b>a|) / (|a>b| + |b>a| + 1)

For a = b (self-loop):
dep(a→a) = |a>a| / (|a>a| + 1)
```
- The result is always between -1 and +1:
    - Close to +1 → a strongly causes b (a → b is a real causal arc)
    - Close to  0 → unclear relationship (could be parallel or coincidental)
    - Close to -1 → b strongly causes a (the arrow should go the other way)
- For example:
```
|a >L b| = 11   (a directly followed by b: 11 times)
|b >L a| = 0    (b directly followed by a: 0 times)
dep(a→b) = (11 - 0) / (11 + 0 + 1) = 11/12 = 0.92 

This is close to 1 — strong evidence that a causes b, not the other way around
```
### Step 3: Build the Dependency Graph
- Now you have two numbers for every activity pair: frequency and dependency. You apply two thresholds to filter out weak/noisy connections:
    - **frequency_threshold**: minimum number of times a→b must occur
    - **dependency_threshold**: minimum dependency value for the arc to be kept
- An arc a → b survives only if both conditions are met. This is exactly Heuristic Mining handles noise: the injected collateral events have low frequency and low dependency compared to real process arcs, so they get filtered out.

### Step 4: Infer XOR vs AND Routing
- The dependency graph only shows which activities are connected. It doesn't tell you whether after activity a you have an XOR-split or an AND-split.
- Heuristic Mining infers this from output binding patterns: what combinations of activities appear together after a
    - Alternatives that rarely appear together suggest XOR 
    - Alternatives that repeatedly co-occur in varying orders suggest AND
- For example:
```
Trace 1: a → b → c → e    ← b and c together
Trace 2: a → c → b → e    ← b and c together (different order)
Trace 3: a → d → e        ← d alone

b and c appear together in varying orders → AND-split (parallel)
b/c and d never appear together → XOR-split (choice between {b,c} and {d})
```
### Step 5: Produce the Workflow Net
- The result is an intermediate Heuristic Net, a graph where:
    - Nodes are activities
    - Edges are the surviving causal arcs
    - Routing logic (XOR/AND) is embedded at each node
- The intermediate Heuristic Net is then converted to a Petri net (Workflow Net) by translating the routing logic into proper places and transitions, which allows formal analysis.

### Why it's called "heuristic"?
- Because nothing here is formally proven. It's all based on educated guesses:
    - Thresholds are chosen by the analyst, not derived mathematically
    - The XOR/AND inference is a heuristic based on co-occurrence patterns
    - There is no guarantee the result is a sound Petri net (unlike Inductive Miner)

### Process Discovery Metrics
- **Fitness**: Measures how well the discovered model can reproduce the behavior observed in the event log. A high fitness value means most traces in the log can be replayed by the model.
- **Precision**: Measures how much extra behavior the model allows beyond what is observed in the log. A high precision value means the model does not permit many unobserved or unrealistic process paths.
- **Generalization**: Measures how well the model can handle new but similar behavior that was not explicitly seen in the log. A high generalization value indicates the model captures the underlying process rather than only memorizing the observed traces.
- **Simplicity**: Measures the complexity of the discovered model. A high simplicity value indicates a smaller and easier-to-understand model with fewer unnecessary constructs.

---

## Implementation

### Sampling
- Due to runtime constraints, a random sample of 5000 cases was taken from the clean log. The noised and recovered logs were then regenerated by applying the pollution and cleaning pipelines developed in Milestone 1 to this sample. This ensured that all three logs were derived from the same set of cases and maintained a noise proportion comparable to that of the original logs.


### Task 1: Compute the dependency graph
- **How it's computed:** use the helper functions in [milestone2/heuristic_miner.ipynb](milestone2/heuristic_miner.ipynb): `compute_frequency_table(df)` builds the |a >L b| table and `compute_dependency(freq_table, a, b)` computes the dependency value

- **Manual verification (example):** the notebook uses the activity pair `O_Created` → `O_Create Offer` as a worked example. To verify manually with the Heuristics Miner value reported by `heu_net.dependency_matrix["O_Created"]["O_Create Offer"]` in the notebook.

### Task 2: Run Heuristics Miner with identical parameters (omit)

- **Parameters used:**
    - `dependency_threshold`: 0.7
    - `min_act_count`: 400
    - `min_dfg_occurrences`: 400

- **Justification:**
    - `dependency_threshold = 0.7` keeps only arcs with reasonably strong directional evidence.
    - `min_act_count = 400` and `min_dfg_occurrences = 400`: These values were chosen based on the dependency graphs of the clean, noised and recovered logs. While the threshold may be high enough to remove some meaningful low-frequency activities and relations from the clean and recovered logs, this is intentionally chosen for some of the noise in noised log introduced in Milestone 1 occurs with relatively high frequency. Therefore, a threshold of 400 provides a reasonable trade-off between preserving important process behavior and filtering out noisy relations in the noised log

### Task 3: Convert to Petri nets and compute quality dimensions
Stats for logs with filtering parameters:

| Log       | Fitness | Precision | Simplicity | Generalization |
| --------- | ------- | --------- | ---------- | -------------- |
| Clean     | 0.9413  | 0.7671    | 0.5766     | 0.9749         |
| Recovered | 0.9031  | 0.5446    | 0.6209     | 0.9477         |
| Noised    | 0.9231  | 0.5069    | 0.5327     | 0.936          |

Stats for logs without filtering parameters:

| Log       | Fitness | Precision | Simplicity | Generalization |
| --------- | ------- | --------- | ---------- | -------------- |
| Clean     | 0.9537  | 0.7466    | 0.5138     | 0.9193         |
| Recovered | 0.9041  | 0.5446    | 0.5502     | 0.8839         |
| Noised    | 0.9137  | 0.3914    | 0.4151     | 0.498          |

Applying frequency and dependency filters significantly improves the quality of a process discovery model when dealing with noised logs. This highlights the primary strength of the heuristic mining method in handling noises.

- **Analysis for logs with filtering parameters**:
    - **Clean Log:** Clean log achieves the best overall quality.
    - **Noised Log:** Noised log has the lowest precision and generalization. Noise changes activity frequencies and dependency values, causing incorrect arcs to survive the thresholds and making the model allow more behavior than intended.
    - **Recovered Log**: The recovered log performs between the clean and noised logs. Some noisy relations were removed, improving the model compared to the noised log. The recovered model also has the highest simplicity score (0.6209), suggesting that several noisy or infrequent relations were removed. However, some valid behavior was also lost, which explains the lower fitness compared to the clean log.

- **Effect of M1 Imperfections**: The noise introduced in Milestone 1 created additional directly-follows relations and changed dependency values. As a result:
    - Some valid arcs fell below the threshold and were removed.
    - Some noisy arcs passed the thresholds and were included.
    - The discovered process structure changed, leading to lower precision and generalization. The recovered log removes part of this effect but does not fully restore the original process structure.

- **Isolated log**: The activity `A_Potential fraud` apears as an isolated branch in all three dependency graphs and Petri nets (disconnected from the main process flow and represented as a separate start-to-end branch in the discovered model). This is caused by the chosen filtering parameters. While the activity itself occurs frequently enough to satisfy min_act_count, its incoming and outgoing relations do not meet the dependency_threshold or min_dfg_occurrences requirements.