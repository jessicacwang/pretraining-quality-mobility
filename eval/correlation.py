import argparse
import json
import gzip
import numpy as np
from scipy.stats import pearsonr
from pathlib import Path
from typing import Dict
from dataclasses import dataclass
from tqdm import tqdm

@dataclass
class Metadata:
    cmi: dict[str, float]
    token_percentile: dict[str, float]
    cluster_5_ids: set[str]
    all_ids: set[str]

def load_metadata(metdata_source: str) -> Metadata:
    """All documents have token percentile values; only a subset have CMI scores."""
    id_to_cmi = dict()
    id_to_percentile = dict()
    cluster_5_ids = set()
    all_ids = set()

    # Stream metadata_source to store id -> cmi if it exists
    with gzip.open(metdata_source, "rt") as s_metadata:
        for s_meta_line in tqdm(s_metadata, desc="source metadata", unit="doc"):
            doc = json.loads(s_meta_line)
            doc_id = doc.get("id")
            doc_percentile = doc.get("token_percentile", 0)
            id_to_percentile[doc_id] = float(doc_percentile)

            doc_cmi = doc.get("cmi", None)
            if doc_cmi is None:
                continue
            id_to_cmi[doc_id] = float(doc_cmi)
            cluster_5_ids.add(doc_id)

    return Metadata(
        cmi=id_to_cmi,
        token_percentile=id_to_percentile,
        cluster_5_ids=cluster_5_ids,
        all_ids=all_ids
    )

def load_audit_results(
        audit_dir: str,
        all_ids: set[str],
        found_value: int,
        target_ids: set[str] | None = None,
) -> Dict[str, int]:
    """Map doc IDs to found/not-found values"""
    results = {}
    found = set()
    # Stream all JSONL files in the path glob
    for shard in tqdm(Path(audit_dir).glob("*.jsonl.gz"),
                      desc="audit shards", unit="shard"):
        with gzip.open(shard, "rt") as f:
            for line in f:
                doc_id = json.loads(line)["id"]
                # If no target_ids exists AND there's no match, move on
                if target_ids is not None and doc_id not in target_ids:
                    continue
                # If target_ids exists + doc match (CMI case)
                # or if target_ids does not exist (percentile case)
                # ...store the doc ID
                results[doc_id] = found_value
                found.add(doc_id)

    # Set the not found value once
    missing_value = int(not found_value)
    # Abstracted away the set of IDs to backfill (either cluster_5_ids or all ids)
    for doc_id in all_ids:
        results.setdefault(doc_id, missing_value)
    return results 

def values(mapping, keys):
    return np.fromiter((mapping[k] for k in keys), dtype=float)

def report_correlation(title: str, x, y):
    corr, p = pearsonr(x, y)
    print("=" * 25, f"{title} correlation", "=" * 25)
    print(f"Correlation: {corr:.4f}")
    print(f"P-value: {p:.4f}")
    print(f"R2 score: {corr**2:.4f}")
    print("=" * 70)
    return

def main(args):
    # Load metadata
    print("Loading metadata for lookup")
    leu_metadata = load_metadata(args.metadata_source)

    # Load audit results
    print("Loading doc IDs' survival for lookup")
    pipeline_results = load_audit_results(
        args.audit_dir,
        leu_metadata.cluster_5_ids,
        found_value=0,
        target_ids=leu_metadata.cluster_5_ids
    )
    langid_results = load_audit_results(
        f"{args.audit_dir}/excluded/1_langid",
        leu_metadata.cluster_5_ids,
        found_value=1,
        target_ids=leu_metadata.cluster_5_ids
    )
    percentile_results = load_audit_results(
        args.audit_dir,
        leu_metadata.all_ids,
        found_value=0
    )
    # Cast keys as lists
    cmi_keys = list(leu_metadata.cluster_5_ids)
    percentile_keys = list(leu_metadata.all_ids)

    # Cast lookups as arrays
    cmi_arr = values(leu_metadata.cmi, cmi_keys)
    cumulative_cluster_5_arr = values(pipeline_results, cmi_keys)
    langid_cluster_5_arr = values(langid_results, cmi_keys)

    percentile_arr = values(leu_metadata.token_percentile, percentile_keys)
    exclusion_arr = values(percentile_results, percentile_keys)

    # Report correlation
    report_correlation("Cumulative", cmi_arr, cumulative_cluster_5_arr)
    report_correlation("LangID", cmi_arr, langid_cluster_5_arr)
    report_correlation("Token percentile", percentile_arr, exclusion_arr)
    
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metadata_source", default="output/preprocess/metadata_source.jsonl.gz"
    )
    parser.add_argument("--audit_dir", default="output/filter")
    args = parser.parse_args()
    main(args)
