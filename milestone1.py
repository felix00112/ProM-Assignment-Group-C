from modules.pollution_logic import *
import pm4py
from pathlib import Path

def main():
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
    
if __name__ == "__main__":
    main()