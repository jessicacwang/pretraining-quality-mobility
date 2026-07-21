import argparse
import json
from typing import Dict, List
from filter.manifest import FilterManifest

FEATURE_POSITIONS = {"cluster": 0, "source": 1, "component": 2, "genre": 3}

def aggregate_by_feature(records: Dict, feature_name: str, filter_fn=None) -> Dict:
    position = FEATURE_POSITIONS[feature_name]

    out = {}

    for key, count in records.items():
        parts = key.split("|")
        if filter_fn and not filter_fn(parts):
            continue
        value = parts[position]
        out[value] = out.get(value, 0) + count
    
    return out

def print_retention_report(stages: List[Dict], feature_names=None, min_count=1):
    feature_names = feature_names or list(FEATURE_POSITIONS)

    for stage in stages:
        stage_name = stage["full_name"]
        stage_total = stage["total"]
        stage_included = stage["included"]["total"]
        stage_retention = stage_included / stage_total if stage_total else float("nan")

        print(f"\n=== {stage_name} - overall retention: {stage_retention:.1%} "
              f"({stage_included}/{stage_total}) ==="
              )
        
        for feature_name in feature_names:
            excluded_by_val = aggregate_by_feature(stage["excluded"]["records"], feature_name)
            included_by_val = aggregate_by_feature(stage["included"]["records"], feature_name)
            all_values = set(excluded_by_val) | set(included_by_val)

            rows = []
            for value in all_values:
                inc = included_by_val.get(value, 0)
                exc = excluded_by_val.get(value, 0)
                total = inc + exc

                if total < min_count:
                    continue 

                retention = inc / total if total else float("nan")
                rows.append((value, retention, inc, total))
            
            rows.sort(key=lambda r: r[1])

            print(f" -- {feature_name} --")
            for value, retention, inc, total in rows:
                # Check if nothing or everything was retained
                flag = "  <-- check this" if retention in (0.0, 1.0) and total >= 10 else ""
                print(f"    {value:>15}: {retention:6.1%} ({inc}/{total}){flag}")
def main(args):
    # Load manifest as nested dictionary
    manifest = FilterManifest(f"{args.output_dir}/manifest.json")

    # Retention is reported...
    stages = list(manifest["steps"]["filter"]["progressive"].values())

    print_retention_report(stages)

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter")
    args = parser.parse_args()
    main(args)