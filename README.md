# ProM Assignment Group C

## Milestone 1 Documentation

This project simulates and resolves common data quality issues in event logs using process mining techniques on the **BPI Challenge 2017 dataset**.

Execute the **pollution script** by running:

```text
notebooks/polluter-script.ipynb
```

Execute the **cleaning script** by running:
```text
notebooks/cleaning-script.ipynb
```

The three resulting **datasets** can be found here:
```text
data/BPI Challenge 217.xes.gz
data/noised.xes.gz
data/recovered.xes.gz
```
In order to run the cleaning script correctly you need to run it within a GitHub Codespace (Secret API Key is needed, which is stored as a secret  in the repo).

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/felix00112/ProM-Assignment-Group-C)

How to use codespaces: https://docs.github.com/en/codespaces/developing-in-a-codespace/developing-in-a-codespace

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
