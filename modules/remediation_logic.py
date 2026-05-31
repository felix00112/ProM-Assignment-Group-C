import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENDPOINT = os.getenv("OPENAI_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(
    base_url=ENDPOINT,
    api_key=API_KEY,
)

#--------------------------------------
# Synonymous Labels
#--------------------------------------
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_similar_labels(
    df: pd.DataFrame,
    threshold: float = 0.65,
    prefix_filter: bool = True
) -> pd.DataFrame:
    """
    Identifies semantically similar event labels using OpenAI embeddings.

    This function computes embeddings for all unique values in the
    'concept:name' column of the input DataFrame and calculates pairwise
    cosine similarity between them. Pairs with similarity above the given
    threshold are returned as potential synonym candidates.

    Optionally, labels can be filtered by prefix (e.g., 'W_', 'A_') to
    avoid comparing activities from different process sections.

    Args:
        df (pd.DataFrame): Input event log dataframe with a 'concept:name' column.
        threshold (float): Similarity threshold for considering two labels as synonyms.
        prefix_filter (bool): If True, only compare labels with the same prefix.
    
    Returns:
        pd.DataFrame: DataFrame containing pairs of similar labels and their similarity scores.
    """    
    labels = df["concept:name"].unique()

    # --- embeddings ---
    embeddings = []
    for l in labels:
        res = openai_client.embeddings.create(
            model=DEPLOYMENT_NAME,
            input=l
        )
        embeddings.append(res.data[0].embedding)
    embeddings = np.array(embeddings)

    # --- similarity pairs ---
    results = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if prefix_filter:
                if labels[i].split("_")[0] != labels[j].split("_")[0]:
                    continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                results.append({
                    "label_1": labels[i],
                    "label_2": labels[j],
                    "similarity": sim
                })
    return pd.DataFrame(results)


def replace_with_most_frequent(
    df: pd.DataFrame,
    synonym_list: list,
    column: str = "concept:name"
) -> pd.DataFrame:
    """
    Replaces a group of synonymous event labels with the most frequent label.

    This function identifies the most common label within a given list of
    synonymous activities and replaces all occurrences of those labels in the
    DataFrame with the most frequent one.

    Args:
        df (pd.DataFrame): Input event log dataframe.
        synonym_list (list): List of synonymous labels to be replaced.
        column (str): Name of the column containing the labels (default is 'concept:name').
        
    Returns:
        pd.DataFrame: Copy of the dataframe with replaced labels.
    """
    df = df.copy()
    subset = df[df[column].isin(synonym_list)]
    most_frequent = subset[column].value_counts().idxmax()
    df.loc[df[column].isin(synonym_list), column] = most_frequent
    return df


#--------------------------------------
# Collateral Events
#--------------------------------------
import pandas as pd

def detect_collateral_events(
    df: pd.DataFrame,
    time_window: str = "5s",
    similarity: bool = False,
    similarity_df: pd.DataFrame = None,
    threshold: float = None
):
    """
    Detects potential collateral events based on temporal proximity
    and optional semantic similarity filtering.

    Args:
        df (pd.DataFrame): Input event log dataframe with 'case:concept:name', 'concept:name', and 'time:timestamp' columns.
        time_window (str): Maximum time difference between events to be considered collateral (e.g., '5s', '1m').
        similarity (bool): If True, apply semantic similarity filtering based on provided similarity_df.
        similarity_df (pd.DataFrame): DataFrame containing pairs of labels and their similarity scores (required if similarity=True).
        threshold (float): Minimum similarity score to consider labels related (required if similarity=True).
    
    Returns:
        pd.DataFrame: DataFrame containing pairs of potentially collateral events with their time difference and similarity score (if applicable).
    """

    df = df.copy()
    df = df.sort_values(["case:concept:name", "time:timestamp"])

    # --- build allowed similarity set ---
    allowed_pairs = set()
    if similarity and similarity_df is not None:
        sim_filtered = similarity_df[similarity_df["similarity"] >= threshold]
        for _, row in sim_filtered.iterrows():
            allowed_pairs.add((row["label_1"], row["label_2"]))
            allowed_pairs.add((row["label_2"], row["label_1"]))  # symmetric

    results = []
    for case_id, group in df.groupby("case:concept:name"):
        group = group.sort_values("time:timestamp")
        for i in range(len(group) - 1):
            row_a = group.iloc[i]
            row_b = group.iloc[i + 1]
            time_diff = row_b["time:timestamp"] - row_a["time:timestamp"]
            if time_diff <= pd.Timedelta(time_window):
                e1 = row_a["concept:name"]
                e2 = row_b["concept:name"]

                # --- semantic filter (optional) ---
                if similarity:
                    if (e1, e2) not in allowed_pairs:
                        continue
                results.append({
                    "case": case_id,
                    "event_1": e1,
                    "event_2": e2,
                    "time_diff": time_diff
                })

    return pd.DataFrame(results)


def merge_collateral_events(df, merge_dict, time_col="time:timestamp"):
    """
    Merges collateral sub-events into a single canonical event.

    For each group of events in merge_dict values:
    - All matching rows are replaced by the key label
    - Other attributes are taken from the earliest event in time

    Args:
        df (pd.DataFrame): Input event log dataframe.
        merge_dict (dict): Dictionary where keys are canonical labels and values are lists of sub-event labels to be merged.
        time_col (str): Name of the timestamp column to determine event order (default is 'time:timestamp').
    
    Returns:
        pd.DataFrame: DataFrame with collateral events merged into canonical events.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    rows_to_drop = []
    rows_to_add = []

    for canonical, subevents in merge_dict.items():
        # process per case
        for case_id, group in df.groupby("case:concept:name"):
            subset = group[group["concept:name"].isin(subevents)]
            if subset.empty:
                continue
            # earliest event per case
            anchor = subset.sort_values(time_col).iloc[0]
            new_row = anchor.copy()
            new_row["concept:name"] = canonical
            rows_to_add.append(new_row)
            rows_to_drop.extend(subset.index.tolist())

    df = df.drop(index=rows_to_drop)
    df = pd.concat([df, pd.DataFrame(rows_to_add)], ignore_index=True)
    df = df.sort_values(["case:concept:name", time_col]).reset_index(drop=True)
    print("Rows to drop:", len(rows_to_drop))
    print("Rows added:", len(rows_to_add))
    return df