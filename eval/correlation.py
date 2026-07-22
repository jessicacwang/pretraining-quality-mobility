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

def exclusion_lookup(output_dir: str, cluster_5_ids: set) -> Dict[str, int]:
    id_to_result = dict()
    included_ids = set()
    # Stream filter results and store if there is a CMI value
    out_dir_path = Path(output_dir)
    for result_file in tqdm(out_dir_path.glob("*.jsonl.gz"), desc="datatrove output", unit="shard"):
        with gzip.open(result_file, "rt") as f_data:
            for f_line in tqdm(f_data, desc="output shard", unit="doc"):
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                if doc_id in cluster_5_ids:
                    id_to_result[doc_id] = 1
                    included_ids.add(doc_id)
    
    # Update id_to_result with remaining id_to_cmi keys
    for k in cluster_5_ids:
        if k not in included_ids:
            id_to_result[k] = 0
    
    return id_to_result

def main(args):
    # Load CMI lookup
    print("Loading metadata for lookup")
    cmi_results, cluster_5_ids = cmi_lookup(args.metadata_source)

    # Load result lookup
    print("Loading 'survived' doc IDs for exclusion lookup")
    filter_results = exclusion_lookup(args.output_dir, cluster_5_ids)

    # Check that lookups are the same length
    assert len(cmi_results) == len(filter_results), f"Lookup sizes differ: {len(cmi_results)}, {len(filter_results)}"

    # Cast as numpy arrays
    print("Casting results as arrays")
    x = np.array([cmi_results[i] for i in cluster_5_ids])
    y = np.array(filter_results[i] for i in cluster_5_ids)

    assert x.size == y.size, f"Array sizes differ: {x.size} vs {y.size}"

    corr, p_value = pearsonr(x, y)
    print(f"Correlation: {corr:3.f}")
    print(f"P-value: {p_value:.3f}")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata_source", default="output/preprocess/metadata_source.jsonl.gz")
    parser.add_argument("--output_dir", default="output/filter")
    args = parser.parse_args()
    main(args)
