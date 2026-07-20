from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import json
import gzip
from collections import Counter


def counter_to_stats(meta_counter: Counter):
    result = {
        "total": sum(meta_counter.values()),
        "by_cluster": {},
        "by_source": {},
        "by_component": {},
        "by_genre": {},
    }

    for key, count in meta_counter.items():
        cluster, source, component, genre = key

        def update_stats(
            subtotal_key: str, subtotal_value: Optional[Dict], joint: Tuple[str]
        ):
            entry = result[subtotal_key].setdefault(
                subtotal_value, {"total": 0, "joint": {}}
            )
            entry["total"] += count
            joint_key = "|".join(str(x) for x in joint)
            entry["joint"][joint_key] = entry["joint"].get(joint_key, 0) + count

        update_stats("by_cluster", cluster, (source, component, genre))
        update_stats("by_source", source, (cluster, component, genre))
        update_stats("by_component", component, (cluster, source, genre))

        genre_val = genre if genre is not None else "null"
        update_stats("by_genre", genre_val, (cluster, source, component))
    return result


def count_excluded(
    executor: str, config: Dict[str, Any], id_to_metadata: Dict[str, Any], algo_key: str
):
    # Initialize excluded metadata
    excluded = list()

    # Define the excluded path
    excluded_dir = Path(f"{config[executor]["output_dir"]}/excluded/{algo_key}/")

    # Loop over all files
    for f in excluded_dir.glob("*.jsonl.gz"):
        with gzip.open(f, "rt") as f_data:
            for f_line in f_data:
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                excluded.append(id_to_metadata[doc_id])

    excluded_counts = Counter(excluded)
    return counter_to_stats(excluded_counts)


def count_included(
    executor: str, config: Dict[str, Any], id_to_metadata: Dict[str, Any], algo_key: str
):
    # Initialize included metadata
    included = list()

    # Define the included path
    included_dir = Path(f"{config[executor]["output_dir"]}/included/")

    # Loop over all files
    for f in included_dir.glob(f"{algo_key}.txt.rank_*"):
        included.extend([id_to_metadata[i.strip()] for i in open(f).readlines()])
    included_counts = Counter(included)
    return counter_to_stats(included_counts)


def update_stats(
    prog_stats: Dict[str, Any],
    algo_stats: Dict[str, Any],
    excluded_stats: Dict[str, Any],
    included_stats: Dict[str, Any],
    algo_key: str,
):

    # Filter datatrove stats for desired items
    target_algo_stats = {
        k: v
        for k, v in algo_stats["stats"].items()
        if k.startswith("dropped") or k == "total" or k == "forwarded"
    }

    # Initialize the current algorithm's progressive stats
    prog_stats[algo_key] = {"full_name": algo_stats["name"]}

    # Update the progressive stats with the total number of dropped/forwarded
    prog_stats[algo_key] |= target_algo_stats

    # Update the progressive stats with subtotals by bucket (cluster, source, component, genre)
    prog_stats[algo_key]["excluded"] = excluded_stats
    prog_stats[algo_key]["included"] = included_stats
    return
