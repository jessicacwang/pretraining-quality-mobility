import argparse
import csv
import math
from filter.manifest import FilterManifest
from typing import Dict, List
from pathlib import Path

FEATURE_POSITIONS = {"cluster": 0, "source": 1, "component": 2, "genre": 3}


def compute_pmi_table(
    excluded_records: Dict, included_records: Dict, feature_name: str
) -> list[dict]:

    position = FEATURE_POSITIONS[feature_name]
    excluded_total = sum(excluded_records.values())
    included_total = sum(included_records.values())
    grand_total = excluded_total + included_total

    p_excluded = excluded_total / grand_total

    marginal_counts = dict()
    joint_counts = dict()

    # Add excluded volumes to both marginal and joint counts
    for key, count in excluded_records.items():
        value = key.split("|")[position]
        marginal_counts[value] = marginal_counts.get(value, 0) + count
        joint_counts[value] = joint_counts.get(value, 0) + count

    # Add included volumes to marginal counts, not joint
    for key, count in included_records.items():
        value = key.split("|")[position]
        marginal_counts[value] = marginal_counts.get(value, 0) + count
        joint_counts.setdefault(value, 0)

    rows = []

    for value, marginal_count in marginal_counts.items():
        joint_count = joint_counts[value]
        p_value = marginal_count / grand_total

        if joint_count == 0:
            pmi = None
        else:
            p_joint = joint_count / grand_total
            pmi = math.log2(p_joint / (p_value * p_excluded))

        rows.append(
            {
                "feature_value": value,
                "pmi": pmi,
                "joint_count": joint_count,
                "marginal_count": marginal_count,
            }
        )

    rows.sort(key=lambda r: (r["pmi"] is not None, r["pmi"]), reverse=True)
    return rows


def write_pmi_csv(rows: List[Dict], out_path: Path):
    fieldnames = ["feature_value", "pmi", "joint_count", "marginal_count"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out_row = dict(row)
            # Leave PMI blank to get pd.NaN rather than writing None
            if out_row["pmi"] is None:
                out_row["pmi"] = ""
            writer.writerow(out_row)


def main(args):
    # Load manifest as nested dictionary
    manifest = FilterManifest(f"{args.output_dir}/manifest.json")

    # Load output dir as a Path
    out_dir_path = Path(args.output_dir)

    # Retrieve cumulative stats
    cumulative_stats = manifest["steps"]["filter"]["cumulative"]

    excluded_records = cumulative_stats["excluded"]["records"]
    included_records = cumulative_stats["included"]["records"]

    # Compute PMI table for each feature
    for feature_name in FEATURE_POSITIONS:
        rows = compute_pmi_table(excluded_records, included_records, feature_name)
        out_path = out_dir_path / f"pmi_{feature_name}.csv"
        write_pmi_csv(rows, out_path)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter")
    args = parser.parse_args()
    main(args)
