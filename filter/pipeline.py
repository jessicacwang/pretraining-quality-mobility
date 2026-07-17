from utils import load_config
from filter.manifest import FilterManifest
import filter.trove as trove
import argparse
import json
from pathlib import Path
import gzip
from collections import defaultdict
from typing import Dict, Any, Tuple, List

ALGORITHMS = {
    1: "1_langid",
    2: "2_gopher_repetition",
    3: "3_gopher_quality",
    4: "4_c4_quality",
    5: "5_fineweb_quality",
}


def register_counts(
    algo_name: str,
    stats: Dict[str, Any],
    count_key: str,
    id_records: List[str],
    id_to_enriched_metadata: Dict[str, Tuple],
    id_to_source_metadata: Dict[str, str],
):
    algo_stats = stats["algorithms"][algo_name]

    for doc_id in id_records:
        doc_cluster, doc_source, doc_component = id_to_enriched_metadata[doc_id]
        doc_genre = id_to_source_metadata.get(doc_id, None)

        # Update algo_stats[algo_name] at all nested levels
        algo_cluster_stats = algo_stats["by_cluster"].setdefault(
            doc_cluster, {"dropped": 0, "forwarded": 0, "total": 0, "by_source": {}}
        )
        algo_source_stats = algo_cluster_stats["by_source"].setdefault(
            doc_source, {"dropped": 0, "forwarded": 0, "total": 0, "by_component": {}}
        )
        algo_comp_stats = algo_source_stats["by_component"].setdefault(
            doc_component, {"dropped": 0, "forwarded": 0, "total": 0, "by_genre": {}}
        )
        algo_cluster_stats[count_key] += 1
        algo_cluster_stats["total"] += 1
        algo_source_stats[count_key] += 1
        algo_source_stats["total"] += 1
        algo_comp_stats[count_key] += 1
        algo_comp_stats["total"] += 1

        if doc_genre:
            algo_genre_stats = algo_comp_stats["by_genre"].setdefault(
                doc_genre, {"dropped": 0, "forwarded": 0, "total": 0}
            )
            algo_genre_stats[count_key] += 1
            algo_genre_stats["total"] += 1
    return


def main(args):
    try:
        # ========================== EXECUTE PIPELINE ==========================
        # Load config
        config = load_config(args.config_path)

        # Prepare output dir
        output_dir = Path(f"{args.output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load manifest
        manifest = FilterManifest(f"{args.output_dir}/manifest.json")
        manifest.start_step("filter")
        manifest.set_args("filter", vars(args))

        try:
            print("Running datatrove...")
            output_path, log_path = trove.run(config, output_dir, manifest)
        except Exception as e:
            print(f"Failed: {e}")
            raise
        # ====================== ACCUMULATE PIPELINE STATS =====================
        print("Collecting datatrove results...")
        stats = {"algorithms": {}}

        trove_results = json.load(open(f"{log_path}/stats.json", "r"))
        # TODO: figure out how to get all dropped_* stats
        for stage_num, trove_stats in enumerate(trove_results[1:-1:2], start=1):
            target_stats = {k: v for k,v in trove_stats['stats'].items() if k.startswith('dropped') or k == 'total' or k=='forwarded'}
            stats["algorithms"][ALGORITHMS[stage_num]] = {
                "full_name": trove_stats["name"],
                "by_cluster": {}
            }
            stats["algorithms"][ALGORITHMS[stage_num]] |= target_stats

        # ======================= ACCUMULATE MORE STATS ========================
        print("Accumulating LEU results...")

        # Map each filter stage to a list of excluded ids
        excluded = defaultdict(list)
        for stage in ALGORITHMS.values():
            with gzip.open(
                f"{output_path}/excluded/{stage}/00000.jsonl.gz", "rt"
            ) as excluded_data:
                for excluded_line in excluded_data:
                    doc = json.loads(excluded_line)
                    doc_id = doc.get("id")
                    excluded[stage].append(doc_id)

        # Stream metadata_enriched to store id -> (cluster, source, component) details
        id_to_enriched_metadata = dict()

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
        id_to_source_metadata = dict()

        with gzip.open(config["source_metadata"], "rt") as s_metadata:
            for s_meta_line in s_metadata:
                doc = json.loads(s_meta_line)
                doc_id = doc.get("id")
                doc_genre = doc.get("genre", None)
                id_to_source_metadata[doc_id] = doc_genre

        # Update stats[filter_stage] with counts by source and by component
        for filter_stage in ALGORITHMS.values():
            excluded_ids = excluded[filter_stage]
            forwarded_ids = [
                i.strip()
                for i in open(
                    f"{output_path}/id_logs/after_{filter_stage}_ids.txt"
                ).readlines()
            ]
            register_counts(
                algo_name=filter_stage,
                stats=stats,
                count_key="dropped",
                id_records=excluded_ids,
                id_to_enriched_metadata=id_to_enriched_metadata,
                id_to_source_metadata=id_to_source_metadata,
            )
            register_counts(
                algo_name=filter_stage,
                stats=stats,
                count_key="forwarded",
                id_records=forwarded_ids,
                id_to_enriched_metadata=id_to_enriched_metadata,
                id_to_source_metadata=id_to_source_metadata,
            )

        # Register completed step
        manifest.end_step("filter")
        manifest.set_audit_stats(stats)
    except Exception as e:
        manifest.fail_step("filter", str(e))
        raise
    finally:
        manifest.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter")
    parser.add_argument("--config_path", default="filter/config/pipeline.json")
    parser.add_argument("--env", choices=["auto", "hyak", "local"], default="auto")
    args = parser.parse_args()
    main(args)
