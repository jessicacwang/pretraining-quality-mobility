from glob import glob
import json
import gzip
import pandas as pd
from pathlib import Path
from tqdm import tqdm 

# METADATA PATHS
SOURCE_METADATA = "output/preprocess/metadata_source.jsonl.gz"
ENRICHED_METADATA = "output/preprocess/metadata_enriched.jsonl.gz"

# Store metadata
doc_to_features = {}

# Load original metadata
with gzip.open(SOURCE_METADATA, "rt") as metadata_source, gzip.open(
    ENRICHED_METADATA, "rt") as metadata_enriched:

    for line_num, (source_line, enriched_line) in enumerate(
        tqdm(zip(metadata_source, metadata_enriched), desc="unified metadata"), 1
    ):
        try:
            meta_s = json.loads(source_line)
            meta_e = json.loads(enriched_line)
        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error at line {line_num}: {e}")
            continue

        if meta_s.get("id") != meta_e.get("id"):
            print(f"Non-matching doc IDs zipped together at {line_num}, skipping")
            continue

        # Assuming valid conditions, build up unified metadata
        doc_id = meta_s.get("id")

        # Skip LinCE docs
        if doc_id.startswith("lince"):
            continue

        doc_to_features[doc_id] = {
            "source": doc_id.split("_")[0],
            "genre": meta_s.get("genre", "null").split("-")[0],
            "component": meta_s.get("component").split("-")[0],
            "cluster_id": meta_e.get("cluster_id"),
            "mobility_v1": meta_e.get("mobility_level_1"),
            "mobility_v2": meta_e.get("mobility_level_2")
        }

# Accumulate filtered docs
doc_to_filter_metadata = {}

# Glob over output/filter/excluded/*
for stage in tqdm(glob("output/filter/excluded/*/"), desc="filter excluded"):
    stage_path = Path(stage)
    # Extract stage number from path stem
    stage_num, stage_name = stage_path.stem.split("_", maxsplit=1)
    stage_num = int(stage_num)

    # Glob over all JSONL data in the excluded set
    for chunk in glob(f"{stage}/*.jsonl.gz"):
        with gzip.open(chunk, "rt") as chunk_gz:
            for line_num, chunk_line in enumerate(tqdm(chunk_gz, leave=False)):
                try:
                    chunk_doc = json.loads(chunk_line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    continue

                # Get doc ID
                doc_id = chunk_doc.get("id")

                if doc_id.startswith("lince"):
                    continue
                # Get original metadata
                doc_metadata = chunk_doc.get("metadata")

                # Remove filepath entry, all others could be useful
                del doc_metadata["file_path"]

                # Store results
                doc_metadata["result"] = "exclude"
                doc_metadata["stage_excluded"] = stage_num
                # Set filter reason to stage name if no specific reason given
                doc_metadata.setdefault("filter_reason", stage_name)
                doc_metadata |= doc_to_features[doc_id]
                doc_to_filter_metadata[doc_id] = doc_metadata 

# Accumulate "survived" docs
for chunk in tqdm(glob("output/filter/*.jsonl.gz"), desc="filter survived"):
    with gzip.open(chunk, "rt") as chunk_gz:
        for line_num, chunk_line in enumerate(tqdm(chunk_gz, leave=False)):
                try:
                    chunk_doc = json.loads(chunk_line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    continue
            
                # Get doc ID
                doc_id = chunk_doc.get("id")

                if doc_id.startswith("lince"):
                    continue

                # Get original metadata
                doc_metadata = chunk_doc.get("metadata")
            
                # Remove filepath entry, all others could be useful
                del doc_metadata["file_path"]
            
                # Store results
                doc_metadata["result"] = "survive"
                doc_metadata["stage_excluded"] = None
                doc_metadata |= doc_to_features[doc_id]
                doc_to_filter_metadata[doc_id] = doc_metadata 

# Convert to dataframe
df = pd.DataFrame.from_dict(doc_to_filter_metadata, orient="index")
df.index.name = "doc_id"
df = df.reset_index() # make doc_id a normal column

df.to_csv("fineweb_output.csv", index=False)