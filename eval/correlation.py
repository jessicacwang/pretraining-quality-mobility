import argparse 
import json
import gzip
import numpy as np
from scipy.stats import pearsonr
from pathlib import Path
from typing import Dict

def cmi_lookup(metdata_source: str) -> Dict[str, int]:
    id_to_cmi = dict()

    # Stream metadata_source to store id -> cmi if it exists
    with gzip.open(metdata_source, "rt") as s_metadata:
        for s_meta_line in s_metadata:
            doc = json.loads(s_meta_line)
            doc_cmi = doc.get("cmi", None)
            if doc_cmi is None:
                continue
            doc_id = doc.get("id")
            id_to_cmi[doc_id] = float(doc_cmi)

    return id_to_cmi

def exclusion_lookup(output_dir: str, id_to_cmi: Dict[str, int]) -> Dict[str, int]:
    id_to_result = dict()

    # Stream filter results and store if there is a CMI value
    out_dir_path = Path(output_dir)
    for result_file in out_dir_path.glob("*.jsonl.gz"):
        with gzip(open(result_file, "rt")) as f_data:
            for f_line in f_data:
                doc = json.loads(f_line)
                doc_id = doc.get("id")
                if doc_id in id_to_cmi:
                    id_to_result[doc_id] = 1
    
    # Update id_to_result with remaining id_to_cmi keys
    for k in id_to_cmi:
        if k not in id_to_result:
            id_to_result[k] = 0
    
    return id_to_result

def main(args):
    # Load CMI lookup
    cmi_results = cmi_lookup(args.metadata_source)

    # Load result lookup
    filter_results = exclusion_lookup(args.output_dir)

    # Cast as numpy arrays
    x = np.array([cmi_results[i] for i in cmi_results])
    y = np.array(filter_results[i] for i in filter_results)

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
