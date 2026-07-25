import gzip
import json
from collections import defaultdict
from tqdm import tqdm

def build(enriched_metadata_file: str, strategy: str) -> tuple[dict, defaultdict]:
    id_to_tokens = dict()
    all_cluster_ids = defaultdict(lambda: {"glowbe": list(), "ice": list(), "lince": list()})
    # Load metadata enriched
    with gzip.open(enriched_metadata_file, "rt") as meta_enriched:
        for line_num, meta_line in enumerate(tqdm(meta_enriched, desc="metadata index"), 1):
            try:
                doc_metadata = json.loads(meta_line)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                continue

            # Extract metadata attributes
            doc_id = doc_metadata.get("id")
            if doc_id is None:
                print(f"Warning: malformed line has no doc ID: {line_num}")
                continue
            doc_source = doc_id.split("_")[0]
            doc_tokens = int(doc_metadata.get("token_count"))
            doc_cluster = str(doc_metadata.get("cluster_id"))

            # Skip LinCE documents iff strategy is balanced, leaving empty list
            if strategy == "balanced" and doc_source == "lince":
                continue

            id_to_tokens[doc_id] = doc_tokens
            all_cluster_ids[doc_cluster][doc_source].append(doc_id)
    return id_to_tokens, all_cluster_ids