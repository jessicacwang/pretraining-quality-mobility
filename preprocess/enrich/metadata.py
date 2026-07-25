import gzip
import json
from collections import defaultdict
from tqdm import tqdm

import preprocess.enrich.features.clustering as clustering
import preprocess.enrich.features.buckets as buckets
import preprocess.enrich.features.tokens as tokens


def build(args, config: dict):
    # initialize token counts for percentiles
    all_token_counts = []

    # initialize stats
    stats = {}

    # intialize global stats separately
    error_counts = defaultdict(int)
    truncated = 0
    # load leu_data and metadata_source for reading
    # open metadata_enriched_tmp for writing
    with gzip.open(args.leu_data, "rt") as leu_data, gzip.open(
        args.metadata_source, "rt"
    ) as metadata_source, gzip.open("metadata_enriched_tmp", "wt") as tmp_gz:

        for line_num, (leu_line, meta_line) in enumerate(
            tqdm(zip(leu_data, metadata_source), desc="unified data"), 1
        ):
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
                # Assign cluster ID using config/preprocess/enrich.json
                doc_cluster_id, doc_corpus, doc_component = clustering.get_id(
                    cluster_config=config,
                    leu_doc=leu_doc,
                    metadata_source=source_metadata,
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
                "token_bucket": token_bucket,
            }
            tmp_gz.write(json.dumps(enriched_record) + "\n")

            # === Accumulate records and update stats
            # record token count and accumulate
            all_token_counts.append(token_count)

            cluster_stats = stats.setdefault(
                doc_cluster_id, {"documents_written": 0, "tokens": 0, "sources": {}}
            )

            cluster_stats["documents_written"] += 1
            cluster_stats["tokens"] += token_count

            source_stats = cluster_stats["sources"].setdefault(
                doc_corpus, {"documents_written": 0, "tokens": 0, "components": {}}
            )

            source_stats["documents_written"] += 1
            source_stats["tokens"] += token_count

            component_stats = source_stats["components"].setdefault(
                doc_component, {"documents_written": 0, "tokens": 0}
            )
            component_stats["documents_written"] += 1
            component_stats["tokens"] += token_count

            # Log to console
            if line_num % 10000 == 0:
                print(f"Processed {line_num} documents")
    return all_token_counts, stats, error_counts, truncated
