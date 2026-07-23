import argparse
import json
import gzip
import numpy as np
from scipy.stats import pearsonr
from pathlib import Path
from typing import Dict
from tqdm import tqdm


def cmi_lookup(metdata_source: str) -> Dict[str, int]:
    id_to_cmi = dict()
    cluster_5_ids = set()

    # Stream metadata_source to store id -> cmi if it exists
    with gzip.open(metdata_source, "rt") as s_metadata:
        for s_meta_line in tqdm(s_metadata, desc="source metadata", unit="doc"):
            doc = json.loads(s_meta_line)
            doc_cmi = doc.get("cmi", None)
            if doc_cmi is None:
                continue
            doc_id = doc.get("id")
            id_to_cmi[doc_id] = float(doc_cmi)
            cluster_5_ids.add(doc_id)

    return id_to_cmi, cluster_5_ids


def exclusion_lookup(audit_dir: str, cluster_5_ids: set) -> Dict[str, int]:
    id_to_result = dict()
    included_ids = set()
    # Stream filter results and store if there is a CMI value
    out_dir_path = Path(audit_dir)
    for result_file in tqdm(
        out_dir_path.glob("*.jsonl.gz"),
        desc="datatrove output",
        unit="shard",
        position=0,
    ):
        with gzip.open(result_file, "rt") as f_data:
            for f_line in tqdm(
                f_data, desc="output shard", unit="doc", position=1, leave=False
            ):
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                if doc_id in cluster_5_ids:
                    id_to_result[doc_id] = 0
                    included_ids.add(doc_id)

    # Update id_to_result with remaining id_to_cmi keys
    for k in tqdm(cluster_5_ids, desc="excluded id fill"):
        if k not in included_ids:
            id_to_result[k] = 1

    return id_to_result

def main(args):
    # Load CMI lookup
    print("Loading metadata for lookup")
    cmi_results, cluster_5_ids = cmi_lookup(args.metadata_source)

    # Load result lookup
    print("Loading doc IDs' survival for lookup")
    pipeline_results = exclusion_lookup(args.output_dir, cluster_5_ids)
    lang_id_results = exclusion_lookup(f"{args.output_dir}/excluded/1_langid", cluster_5_ids)
    # Cast as numpy arrays, in the same order
    print("Casting results as arrays")
    keys = list(cluster_5_ids)
    x = np.array([cmi_results[k] for k in keys])
    y = np.array([pipeline_results[k] for k in keys])
    z = np.array([lang_id_results[k] for k in keys])

    assert x.size == z.size, f"Array sizes differ: {x.size} vs {y.size}"

    y_corr, y_p_value = pearsonr(x, y)
    print("=" * 30, "Cumulative correlation", "=" * 30)
    print(f"Correlation: {y_corr:.4f}")
    print(f"P-value: {y_p_value:.4f}")
    print(f"R2 score: {y_corr**2:.4f}")
    print("=" * 70)

    z_corr, z_p_value = pearsonr(x, z)
    print("=" * 30, "LangID correlation", "=" * 30)
    print(f"Correlation: {z_corr:.4f}")
    print(f"P-value: {z_p_value:.4f}")
    print(f"R2 score: {z_corr**2:.4f}")
    print("=" * 70)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metadata_source", default="output/preprocess/metadata_source.jsonl.gz"
    )
    parser.add_argument("--output_dir", default="output/filter")
    args = parser.parse_args()
    main(args)
