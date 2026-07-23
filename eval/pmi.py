import argparse
import csv
import math
from filter.manifest import FilterManifest
from typing import Dict, List
from pathlib import Path
from eval.features import FEATURE_POSITIONS, aggregate_by_features

def compute_pmi_table(
    excluded_records: Dict, included_records: Dict, feature_names: List[str]
) -> List[Dict]:
    excluded_by_val = aggregate_by_features(excluded_records, feature_names)
    included_by_val = aggregate_by_features(included_records, feature_names)

    excluded_total = sum(excluded_by_val.values())
    included_total = sum(included_by_val.values())
    grand_total = excluded_total + included_total

    p_excluded = excluded_total / grand_total

    all_values = set(excluded_by_val) | set(included_by_val)
    
    rows = []

    for value in all_values:
        marginal_count = excluded_by_val.get(value, 0) + included_by_val.get(value, 0)
        joint_count = excluded_by_val.get(value, 0)
        p_value = marginal_count / grand_total

        if joint_count == 0:
            pmi = None
            npmi = None
        else:
            p_joint = joint_count / grand_total
            pmi = math.log2(p_joint / (p_value * p_excluded))
            npmi = pmi / math.log2(p_joint) * -1
        rows.append(
            {
                "feature_value": value,
                "pmi": pmi,
                "npmi": npmi,
                "joint_count": joint_count,
                "marginal_count": marginal_count,
            }
        )

    rows.sort(key=lambda r: (r["pmi"] is not None, r["pmi"]), reverse=True)
    return rows


def write_pmi_csv(rows: List[Dict], out_path: Path):
    fieldnames = ["feature_value", "pmi", "npmi", "joint_count", "marginal_count"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out_row = dict(row)
            # Leave PMI blank to get pd.NaN rather than writing None
            if out_row["pmi"] is None:
                out_row["pmi"] = ""
            if out_row["npmi"] is None:
                out_row["npmi"] = ""
            writer.writerow(out_row)


def main(args):
    # Load manifest as nested dictionary
    manifest = FilterManifest(f"{args.audit_dir}/manifest.json")

    # Load output dir as a Path
    out_dir_path = Path(args.output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Retrieve cumulative stats
    cumulative_stats = manifest["steps"]["filter"]["cumulative"]

    excluded_records = cumulative_stats["excluded"]["records"]
    included_records = cumulative_stats["included"]["records"]

    # Compute PMI table for each feature
    for feature_name in FEATURE_POSITIONS:
        rows = compute_pmi_table(excluded_records, included_records, [feature_name])
        out_path = out_dir_path / f"{feature_name}.csv"
        write_pmi_csv(rows, out_path)

    # Since GloWbe and ICE data share component labels, we can separate this out
    rows = compute_pmi_table(excluded_records, included_records, ["source", "component"])
    write_pmi_csv(rows, out_dir_path / "source_component.csv")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit_dir", default="output/filter/audit")
    parser.add_argument("--output_dir", default="output/eval/pmi")
    args = parser.parse_args()
    main(args)
