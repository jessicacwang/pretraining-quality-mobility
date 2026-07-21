import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Tuple


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


def counter_to_stats(meta_counter: Counter):
    result = {"total": sum(meta_counter.values()), "records": {}}

    for (cluster, source, component, genre), count in meta_counter.items():
        genre_val = genre if genre is not None else "null"
        key = "|".join(str(x) for x in (cluster, source, component, genre_val))
        result["records"][key] = result["records"].get(key, 0) + count

    return result


def get_counts_from_excluded(id_to_metadata: Dict[str, Tuple], working_dir: Path):
    excluded_ids = list()
    excluded = list()

    for f in working_dir.glob("*.jsonl.gz"):
        with gzip.open(f, "rt") as f_data:
            for f_line in f_data:
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                excluded_ids.append(doc_id)
                excluded.append(id_to_metadata[doc_id])

    included = [id_to_metadata[i] for i in id_to_metadata if i not in excluded_ids]

    included_counts = Counter(included)
    excluded_counts = Counter(excluded)
    return counter_to_stats(included_counts), counter_to_stats(excluded_counts)


def get_counts_from_included(id_to_metadata: Dict[str, Tuple], working_dir: Path):
    included_ids = list()
    included = list()

    for f in working_dir.glob("*.jsonl.gz"):
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
