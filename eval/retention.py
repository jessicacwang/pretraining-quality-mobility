import argparse
import json
import math
from typing import Dict
from filter.manifest import FilterManifest

FEATURE_POSITIONS = {"cluster": 0, "source": 1, "component": 2, "genre": 3}


def aggregate_by_feature(records: Dict, feature_name: str) -> Dict:
    position = FEATURE_POSITIONS[feature_name]

    out = {}

    for key, count in records.items():
        parts = key.split("|")
        value = parts[position]
        out[value] = out.get(value, 0) + count

    return out


def print_retention_report(stages: Dict, feature_names=None, min_count=1):
    feature_names = feature_names or list(FEATURE_POSITIONS)

    for _, stage in stages.items():
        stage_name = stage["full_name"]
        stage_total = stage["total"]["total"]
        stage_included = stage["forwarded"]["total"]
        stage_retention = stage_included / stage_total if stage_total else float("nan")
        stage_lrp = -1 * math.log(stage_retention) if stage_retention else float("nan")

        print(
            f"\n=== {stage_name} - overall retention: {stage_retention:.1%}; LRP: {stage_lrp:.4f} "
            f"({stage_included}/{stage_total}) ==="
        )

        for feature_name in feature_names:
            excluded_by_val = aggregate_by_feature(
                stage["excluded"]["records"], feature_name
            )
            included_by_val = aggregate_by_feature(
                stage["included"]["records"], feature_name
            )
            all_values = set(excluded_by_val) | set(included_by_val)

            rows = []
            for value in all_values:
                inc = included_by_val.get(value, 0)
                exc = excluded_by_val.get(value, 0)
                total = inc + exc

                if total < min_count:
                    continue

                retention = inc / total if total else float("nan")
                if retention == 0:
                    lrp = float("nan")
                else:
                    lrp = -1 * math.log(retention)
                rows.append((value, retention, lrp, inc, total))

            rows.sort(key=lambda r: (r[0], r[1]))

            print(f" -- {feature_name} --")
            for value, retention, lrp, inc, total in rows:
                print(f"    {value:>15}: {retention:6.1%} {lrp:.4f} ({inc}/{total})")


def main(args):
    # Load manifest as nested dictionary
    manifest = FilterManifest(f"{args.output_dir}/manifest.json")

    # Retention is reported...
    stages = manifest["steps"]["filter"]["progressive"]

    print_retention_report(stages)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter/audit")
    args = parser.parse_args()
    main(args)
