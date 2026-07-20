import json
import gzip
from pathlib import Path
from collections import Counter
from typing import Optional, Dict, Tuple, Any


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


def count_included_excluded(
    id_to_metadata: Dict[str, Any], output_dir: Path, file_pattern: str
):
    included_ids = list()
    included = list()

    for f in output_dir.glob(file_pattern):
        with gzip.open(f, "rt") as f_data:
            for f_line in f_data:
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                included_ids.append(doc_id)
                included.append(id_to_metadata[doc_id])

    excluded = [id_to_metadata[i] for i in id_to_metadata if i not in included_ids]

    included_counts = Counter(included)
    excluded_counts = Counter(excluded)

    return counter_to_stats(included_counts), counter_to_stats(excluded_counts)


def update_stats(
    cumul_stats: Dict[str, Any],
    id_to_metadata: Dict[str, Tuple],
    output_dir: Path,
    file_pattern: str,
):
    included_stats, excluded_stats = count_included_excluded(
        id_to_metadata, output_dir, file_pattern
    )
    cumul_stats["included"] = included_stats
    cumul_stats["excluded"] = excluded_stats
    return
