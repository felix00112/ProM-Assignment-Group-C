import random
import pandas as pd
from pathlib import Path

#--------------------------------------
# Synonymous Labels
#--------------------------------------
SYNONYMS = {
    "W_Complete application": ["W_Finish application", "W_Finalize application"],
}

def add_synonymous_labels(df: pd.DataFrame, fraction: float = 0.3) -> pd.DataFrame:
    """Add synonymous labels randomly to a fraction of the occurrences of specified activities"""
    df = df.copy()
    for original, alternatives in SYNONYMS.items():
        original_rows = df[df["concept:name"] == original]

        if original_rows.empty:
            print(f"[synonymous_labels] Warning: '{original}' not found in log, skipping.")
            continue

        sampled_idx = original_rows.sample(frac=fraction).index
        mask = (df["concept:name"] == original) & (df.index.isin(sampled_idx))
        df.loc[mask, "concept:name"] = [random.choice(alternatives) for _ in range(mask.sum())]

        print(f"[synonymous_labels] Replaced {mask.sum()} / {len(original_rows)} "
              f"occurrences of '{original}'")

    return df


#--------------------------------------
# Collateral Events
#--------------------------------------
# Sub-steps that logically make up "W_Complete application" - Action = Obtained, lifecycle:transition = start
COLLATERAL_SUBSTEPS = [
    "W_Precheck application: Applicant Identity",
    "W_Precheck application: Form Completeness",
    "W_Precheck application: Credit History",
]

def add_collateral_events(
    df: pd.DataFrame, 
    concept_name: str = "W_Complete application", 
    action: str = "Obtained", 
    lifecycle_transition: str = "start", 
    fraction: float = 0.001
) -> pd.DataFrame:
    """
    Inject collateral sub-steps for a fraction of cases.
    Each injected sub-step inherits all column values from the anchor event
    except 'concept:name', 'time:timestamp', and 'start_timestamp', which
    are updated to reflect the sub-step identity and timing (1 second apart)
    
    Args:
        df (pd.DataFrame): Event log dataframe
        concept_name (str): Activity name to use as the injection anchor
        action (str): The 'Action' column value of the anchor event
        lifecycle_transition (str): The 'lifecycle:transition' value of the anchor event
        fraction (float): Fraction of eligible cases to inject sub-steps into

    Returns:
        pd.DataFrame: Copy of the dataframe with injected collateral sub-step rows    
    """
    df = df.copy()
    new_rows = []

    # Get cases that contain W_Complete application with Obtained/start
    target_cases = df[
        (df["concept:name"] == concept_name) &
        (df["Action"] == action) &
        (df["lifecycle:transition"] == lifecycle_transition)
    ]["case:concept:name"].unique()

    if len(target_cases) == 0:
        print(f"[collateral_events] Warning: No matching anchor events found, returning unchanged df.")
        return df
    n_sampled = max(1, int(len(target_cases) * fraction))
    sampled_cases = random.sample(list(target_cases), n_sampled)

    for case_id in sampled_cases:
        # Find specifically the Obtained/start event
        anchor = df[
            (df["case:concept:name"] == case_id) &
            (df["concept:name"] == concept_name) &
            (df["Action"] == action) &
            (df["lifecycle:transition"] == lifecycle_transition)
        ].iloc[0]

        anchor_time = anchor["time:timestamp"]

        # Inject sub-steps after the start event, 1 second apart
        for i, substep in enumerate(COLLATERAL_SUBSTEPS):
            new_rows.append({
                **anchor.to_dict(),
                "concept:name": substep,
                "time:timestamp": anchor_time + pd.Timedelta(seconds=i + 1),
                "start_timestamp": anchor_time + pd.Timedelta(seconds=i + 1),
            })

    new_df = pd.DataFrame(new_rows)
    return pd.concat([df, new_df]).sort_values(
        ["case:concept:name", "time:timestamp"]
    ).reset_index(drop=True)
    

#--------------------------------------
# Scattered Cases
#--------------------------------------
def add_scattered_cases(
    df: pd.DataFrame, 
    output_path: Path | str, 
    concept_name: str = "valid"
) -> pd.DataFrame:
    """
    Simulate scattered cases by removing all events containing given word
    in concept:name and saving them to a separate CSV (simulating another system)
    Args:
        df (pd.DataFrame): Event log dataframe
        output_path (str or Path): File path where the removed events will be
                                   saved as a CSV.
        concept_name (str): Keyword to match against 'concept:name' (case-insensitive).
    Returns:
        pd.DataFrame: Copy of the dataframe with matching events removed
    """
    df = df.copy()
    if isinstance(output_path, str):
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Find all rows containing the concept name (case-insensitive)
    mask = df["concept:name"].str.contains(concept_name, case=False, na=False)
    
    if mask.sum() == 0:
        print(f"[scattered_cases] Warning: No events found containing '{concept_name}', returning unchanged df.")
        return df

    # Split into two
    scattered_df = df[mask]
    clean_df = df[~mask]

    # Save the removed events to separate CSV
    scattered_df.to_csv(output_path, index=False)
    print(f"Saved removed events to: {output_path}")

    return clean_df