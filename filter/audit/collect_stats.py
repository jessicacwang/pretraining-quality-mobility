from typing import List, Dict, Tuple, Any

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