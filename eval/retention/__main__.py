import argparse
import csv
import json
from pathlib import Path
from typing import Dict

import eval.retention.report as report 
from eval.retention.strata import build_strata
from eval.retention.sankeys import build_all_sankeys
from eval.retention.plot_data import build_all_series 

from filter.manifest import FilterManifest

CSV_FIELDNAMES = ["value", "stage", "stage_name", "included", "total", "retention", "lrp", "cumulative_lrp"]

def write_csvs(all_series: Dict, output_dir: Path):
    csv_dir = output_dir / Path("plot_data/")
    csv_dir.mkdir(parents=True, exist_ok=True)

    for key, rows in all_series.items():
        path = csv_dir / Path(f"retention_{key}.csv")
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
    return

def write_jsons(sankeys: Dict, output_dir: Path):
    sankey_file = output_dir / Path("sankeys.json")
    with open(sankey_file, "w") as f:
        json.dump(sankeys, f, indent=2)
    return 

def main(args):
    # Load manifest as nested dictionary
    manifest = FilterManifest(f"{args.audit_dir}/manifest.json")

    stages = manifest["steps"]["filter"]["progressive"]

    # Load output dir as a Path
    out_dir_path = Path(args.output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Log report for sanity check/skim results
    if not args.quiet:
        report.run(stages, min_count=args.min_count)

    # Build all stratifications of interest
    strata = build_strata()

    # Format these as Sankey JSONs
    sankeys = build_all_sankeys(stages, strata)
    write_jsons(sankeys, out_dir_path)

    # Also generate RR + LRP CSV data for line + waterfall graphs
    plot_data = build_all_series(stages, strata)
    write_csvs(plot_data, out_dir_path)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit_dir", default="output/filter/audit")
    parser.add_argument("--output_dir", default="output/eval/retention")
    parser.add_argument("--top_n", type=int, default=None)
    parser.add_argument("--min_count", type=int, default=1)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    main(args)
