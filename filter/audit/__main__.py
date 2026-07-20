import argparse
import json
import gzip
from utils import load_config
from filter.manifest import FilterManifest
import filter.audit.progressive as progressive
import filter.audit.cumulative as cumulative
from typing import Dict, Any, Tuple
from pathlib import Path


def metadata_lookup(config: Dict[str, Any]) -> Tuple[Dict, Dict]:
    id_to_enriched_metadata = dict()
    id_to_source_metadata = dict()

    # Stream metadata_enriched to store id -> (cluster, source, component) details
    with gzip.open(config["enriched_metadata"], "rt") as e_metadata:
        for e_meta_line in e_metadata:
            doc = json.loads(e_meta_line)
            doc_id = doc.get("id")
            doc_cluster = doc.get("cluster_id")
            doc_source, doc_component = doc_id.split(":")[0].split("_", maxsplit=1)

            id_to_enriched_metadata[doc_id] = (
                doc_cluster,
                doc_source,
                doc_component,
            )

    # Stream metadata_source to store id -> genre if it exists
    with gzip.open(config["source_metadata"], "rt") as s_metadata:
        for s_meta_line in s_metadata:
            doc = json.loads(s_meta_line)
            doc_id = doc.get("id")
            doc_genre = doc.get("genre", None)
            id_to_source_metadata[doc_id] = doc_genre

    # Concatenate results
    return {
        i: id_to_enriched_metadata[i] + (id_to_source_metadata[i],)
        for i in id_to_enriched_metadata
    }


def main(args):
    # Load config
    config = load_config(args.config_path)

    # Load manifest
    manifest = FilterManifest(f"{args.output_dir}/manifest.json")
    manifest.start_step("filter")
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

        for n, algo_stats in enumerate(datatrove_stats[1:-1:2], start=1):
            algo_key = config["algorithms"][str(n)]

            # Load all excluded document IDs for this algorithm
            algo_excluded = progressive.count_excluded(
                args.executor, config, id_to_metadata, algo_key
            )

            # Load all included document IDs for this algorithm
            algo_included = progressive.count_included(
                args.executor, config, id_to_metadata, algo_key
            )

            # Update progressive stats
            progressive.update_stats(
                stats["progressive"], algo_stats, algo_excluded, algo_included, algo_key
            )

        # ==================== ACCUMULATE CUMULATIVE STATS =====================
        cumulative.update_stats(
            stats["cumulative"], id_to_metadata, Path(args.output_dir), "*.jsonl.gz"
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
    parser.add_argument("--output_dir", default="output/filter")
    parser.add_argument("--config_path", default="config/filter/pipeline.json")
    parser.add_argument("--executor", choices=["slurm", "local"], default="slurm")

    args = parser.parse_args()
    main(args)
