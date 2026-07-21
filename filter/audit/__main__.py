import argparse
import json
from utils import load_config
from filter.manifest import FilterManifest
import filter.audit.progressive as progressive
import filter.audit.cumulative as cumulative
from filter.audit.utils import metadata_lookup
from pathlib import Path


def main(args):
    # Load config
    config = load_config(args.config_path)

    # Load manifest
    manifest = FilterManifest(f"{args.output_dir}/manifest.json")
    manifest.set_args("filter", vars(args))

    # Initialize stats
    stats = {"progressive": {}, "cumulative": {}}

    # Load metadata
    id_to_metadata = metadata_lookup(config)

    try:
        # ==================== ACCUMULATE PROGRESSIVE STATS ====================
        log_path = config[args.executor]["log_dir"]
        # Load datatrove stats
        datatrove_stats = json.load(open(f"{log_path}/stats.json", "r"))

        for n, algo_stats in enumerate(datatrove_stats[1:-1], start=1):
            algo_key = config["algorithms"][str(n)]
            excluded_dir = Path(
                f"{config[args.executor]["output_dir"]}/excluded/{algo_key}/"
            )
            # Update progressive stats
            progressive.update_stats(
                stats["progressive"],
                algo_stats,
                id_to_metadata,
                excluded_dir,
                algo_key,
            )

        # ==================== ACCUMULATE CUMULATIVE STATS =====================
        cumulative.update_stats(
            stats["cumulative"], id_to_metadata, Path(args.output_dir)
        )

        # Register completed step
        manifest.end_step("filter")
        manifest.set_audit_stats(stats)
    except Exception as e:
        manifest.fail_step("filter", str(e))
        raise
    finally:
        manifest.save()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter/")
    parser.add_argument("--config_path", default="config/filter/pipeline.json")
    parser.add_argument("--executor", choices=["slurm", "local"], default="slurm")

    args = parser.parse_args()
    main(args)
