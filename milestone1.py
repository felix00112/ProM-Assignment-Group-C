from modules.pollution_logic import *
from modules.remediation_logic import *
import pm4py
from pathlib import Path

def main():
    ############################
    # Pollution Pipeline
    ############################
    print("Loading log...")
    log = pm4py.read_xes(str(Path(__file__).parent / 'data' / 'BPI Challenge 2017.xes.gz'))
    df = pm4py.convert_to_dataframe(log)
    print(f"Original log: {len(df)} events, {df['case:concept:name'].nunique()} cases")

    # Apply pollutions
    print("\nApplying synonymous labels...")
    polluted_df = add_synonymous_labels(df)

    print("Applying collateral events...")
    polluted_df = add_collateral_events(polluted_df)

    print("Applying scattered cases...")
    polluted_df = add_scattered_cases(
        polluted_df, 
        output_path=Path(__file__).parent / 'data' / 'polluted_data' / 'scattered_events_validation.csv',
        concept_name="valid"
    )
    
    # 3 other patterns can be added here...

    print(f"\nPolluted log: {len(polluted_df)} events, {polluted_df['case:concept:name'].nunique()} cases")
    
    # Convert back to event log object
    output_dir = Path(__file__).parent / 'data' / 'polluted_data'
    output_dir.mkdir(parents=True, exist_ok=True)
    polluted_log = pm4py.convert_to_event_log(polluted_df)
    pm4py.write_xes(polluted_log, output_dir / 'polluted_log.xes')
    print(f"Done — saved to {output_dir / 'polluted_log.xes'}")
    
    ############################
    # Remediation Pipeline
    ############################
    polluted_log = pm4py.read_xes(str(Path(__file__).parent / 'data' / 'polluted_data' / 'polluted_log.xes'))
    polluted_df = pm4py.convert_to_dataframe(polluted_log)
    
    print("\nFinding similar labels...")
    result = find_similar_labels(polluted_df, threshold=0.65, prefix_filter = True)
    SYNONYMOUS_LABELS = ["W_Complete application", "W_Finish application", "W_Finalize application"]
    print(f"Identified synonyms: {SYNONYMOUS_LABELS}")
    cleaned_df = replace_with_most_frequent(polluted_df, SYNONYMOUS_LABELS)

    print("Merging collateral events...")
    result_for_collateral = result[~result['label_1'].isin(SYNONYMOUS_LABELS)]
    collateral_df  = detect_collateral_events(polluted_df, time_window="5s", similarity=True, similarity_df=result_for_collateral, threshold=0.65)
    print(f"Identified collateral events: {set(collateral_df['event_1'].unique()) | set(collateral_df['event_2'].unique())}")
    COLLATERAL_LABELS_DICT = {
    "W_Precheck application": [
        "W_Precheck application: Applicant Identity",
        "W_Precheck application: Form Completeness",
        "W_Precheck application: Credit History"
    ]
    }
    cleaned_df = merge_collateral_events(cleaned_df, COLLATERAL_LABELS_DICT)
    
    # 3 other patterns can be added here...
    
    # Convert back to event log object
    cleaned_log = pm4py.convert_to_event_log(cleaned_df)
    output_dir = Path(__file__).parent / 'data' / 'cleaned_data'
    output_dir.mkdir(parents=True, exist_ok=True)
    pm4py.write_xes(cleaned_log, output_dir / 'cleaned_log.xes')
    print(f"Done — saved to {output_dir / 'cleaned_log.xes'}")
    
if __name__ == "__main__":
    main()