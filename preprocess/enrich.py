"""Derive metadata fields not inherent to source datasets (token_count, token_percentile, etc.) and update output/preprocess/metadata.jsonl.gz"""
from preprocess.manifest import PreprocessManifest
from preprocess.features import clustering, buckets, percentiles, tokens
import argparse
from pathlib import Path
from preprocess.utils import load_config
from collections import defaultdict
import gzip
import json


def main(args):
    # load unify config
    config = load_config(args.config_path)

    # Prepare output dir
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # load Manifest, initializing if it doesn't exist
    manifest = PreprocessManifest(f"{args.output_dir}/manifest.json")
    
    manifest.start_step("enrich", args.notes)
    manifest.set_args("enrich", vars(args))

    output_files = {
        "metadata": f"{args.output_dir}/metadata_enriched.jsonl.gz",
    }
    manifest.set_output_files("enrich", output_files)
    
    # initialize token counts for percentiles
    all_token_counts = []

    # initialize stats
    stats = {}

    # intialize global stats separately
    error_counts = defaultdict(int)
    truncated = 0

    try:
        # ========================== PASS 1: Local fields ==========================
        # load leu_data and metadata_source for reading
        # open metadata_enriched_tmp for writing
        with gzip.open(args.leu_data, "rt") as leu_data, \
            gzip.open(args.metadata_source, "rt") as metadata_source, \
            gzip.open("metadata_enriched_tmp", "wt") as tmp_gz:
            
            for line_num, (leu_line, meta_line) in enumerate(zip(leu_data, metadata_source), 1):
                try:
                    leu_doc = json.loads(leu_line)
                    source_metadata = json.loads(meta_line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    continue
                
                # check IDs match
                if leu_doc.get("id") != source_metadata.get("id"):
                    error_counts["id_mismatch"] += 1
                    continue
                
                # check for empty text
                text = leu_doc.get("text")
                if not text or not text.strip():
                    error_counts["empty_text"] += 1
                    continue

                # ==== Clustering
                try:
                    # Assign cluster ID using preprocess/config/enrich.json
                    doc_cluster_id, doc_corpus, doc_component = clustering.get_id(
                        cluster_config=config,
                        leu_doc=leu_doc,
                        metadata_source=source_metadata
                    )
                except Exception as e:
                    error_counts["clustering_failed"] += 1
                    continue

                # ==== Tokens
                # tokenize
                try:
                    # Get token count
                    token_count, doc_truncated = tokens.get_count(leu_doc.get("text"))
                    if doc_truncated:
                        truncated += 1
                except Exception as e:
                    error_counts["tokenization_failed"] += 1
                    continue
                
                # assign length bucket
                try:
                    token_bucket = buckets.get_bucket(token_count)
                except Exception as e:
                    error_counts["bucketing_failed"] += 1
                    continue

                # write enriched record to tmp file
                enriched_record = {
                    "id": leu_doc.get("id"),
                    "cluster_id": doc_cluster_id,
                    "token_count": token_count,
                    "token_bucket": token_bucket
                }
                tmp_gz.write(json.dumps(enriched_record) + "\n")

                # === Accumulate records and update stats
                # record token count and accumulate
                all_token_counts.append(token_count)

                cluster_stats = stats.setdefault(doc_cluster_id, {
                    "documents_written": 0,
                    "tokens": 0,
                    "sources": {}
                })

                cluster_stats["documents_written"] += 1
                cluster_stats["tokens"] += token_count

                source_stats = cluster_stats["sources"].setdefault(doc_corpus, {
                    "documents_written": 0,
                    "tokens": 0,
                    "components": {}
                })

                source_stats["documents_written"] += 1
                source_stats["tokens"] += token_count

                component_stats = source_stats["components"].setdefault(doc_component, {
                    "documents_written": 0,
                    "tokens": 0
                })
                component_stats["documents_written"] += 1
                component_stats["tokens"] += token_count

                # Log to console
                if line_num % 10000 == 0:
                    print(f"Processed {line_num} documents")
                    manifest.save()
                    
        # ========================== PASS 2: Global fields =========================
        # Pre-compute percentile lookups
        token_percentiles = percentiles.compute_lookups(all_token_counts)

        # open metadata_enriched_final (write) and enriched_tmp (read)
        with gzip.open("metadata_enriched_tmp", "rt") as tmp_gz, \
            gzip.open(f"{args.output_dir}/metadata_enriched.jsonl.gz", "wt") as meta_gz:
            
            # for document in metata_enriched_tmp
            for line_num, tmp_line in enumerate(tmp_gz, 1):
                try:
                    tmp_doc = json.loads(tmp_line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    continue

                doc_percentile = token_percentiles[tmp_doc.get("token_count")]
                meta_gz.write(json.dumps(tmp_doc | {"token_percentile": doc_percentile}) + "\n")

        # === Update manifest
        manifest.set_enrich_stats(
            stats=stats, errors=dict(error_counts), truncated=truncated, 
            cluster_descriptions=config["descriptions"])
        manifest.end_step("enrich")
    except Exception as e:
        manifest.fail_step("enrich", str(e))
        raise
    finally:
        manifest.save()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", default="preprocess/config/enrich.json")
    parser.add_argument("--output_dir", default="output/preprocess")
    parser.add_argument("--leu_data", default="output/preprocess/leu_data.jsonl.gz")
    parser.add_argument("--metadata_source", default="output/preprocess/metadata_source.jsonl.gz")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    main(args)
