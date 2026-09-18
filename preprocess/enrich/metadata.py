import gzip
import json
from collections import defaultdict
from tqdm import tqdm

import preprocess.enrich.features.clustering as clustering
import preprocess.enrich.features.mobility as mobility
import preprocess.enrich.features.buckets as buckets
import preprocess.enrich.features.tokens as tokens


def build(args, config: dict):
    # initialize token counts for percentiles
    all_token_counts = []

    # initialize stats
    stats = {"distribution": {}, "mobility_v1": {}, "mobility_v2": {}}

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
                    cluster_config=config["distribution"],
                    leu_doc=leu_doc,
                    source_metadata=source_metadata,
                )
            except Exception as e:
                error_counts["clustering_failed"] += 1
                continue

            # ==== Level assignment
            try:
                # Assign mobility level using config/preprocess/enrich.json
                doc_mobility_v1, doc_mobility_v2, doc_genre = mobility.get_level(
                    level_config=config["mobility"],
                    leu_doc=leu_doc,
                    source_metadata=source_metadata,
                )
            except Exception as e:
                error_counts["mobility_failed"] += 1
                continue

            # ==== Tokens
            # tokenize
            try:
                # Get token count
                token_count, doc_truncated = tokens.get_dolma_count(leu_doc.get("text"))
                if doc_truncated:
                    truncated += 1
            except Exception as e:
                error_counts["dolma_tokenization_failed"] += 1
                continue

            try:
                # Get whitespace and char count
                whitespace_count = tokens.get_whitespace_count(leu_doc.get("text"))
                char_count = tokens.get_char_count(leu_doc.get("text"))
            except Exception as e:
                error_counts["text_tokenization_failed"] += 1
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
                "mobility_level_1": doc_mobility_v1,
                "mobility_level_2": doc_mobility_v2,
                "token_count": token_count,
                "token_bucket": token_bucket,
                "word_count": whitespace_count,
                "char_count": char_count,
            }
            tmp_gz.write(json.dumps(enriched_record) + "\n")

            # === Accumulate records and update stats
            # record token count and accumulate
            all_token_counts.append(token_count)

            # === Distribution stats
            build_stats(
                stats=stats,
                token_count=token_count,
                doc_corpus=doc_corpus,
                doc_cluster_id=doc_cluster_id,
                doc_mobility_v1=doc_mobility_v1,
                doc_mobility_v2=doc_mobility_v2,
                doc_component=doc_component,
                doc_genre=doc_genre,
            )
    return all_token_counts, stats, error_counts, truncated


def increment(stat_dict: dict, k: str, count: int = 1):
    stat_dict[k] += count
    return


def build_stats(
    stats: dict,
    token_count: int,
    doc_corpus: str,
    doc_cluster_id: str,
    doc_mobility_v1: str,
    doc_mobility_v2: str,
    doc_component: str,
    doc_genre: str,
):
    # Initialize nested dict key pointers
    # === Distribution
    cluster_stats = stats["distribution"].setdefault(
        doc_cluster_id, {"documents_written": 0, "tokens": 0, "sources": {}}
    )
    cluster_source_stats = cluster_stats["sources"].setdefault(
        doc_corpus, {"documents_written": 0, "tokens": 0, "components": {}}
    )
    component_stats = cluster_source_stats["components"].setdefault(
        doc_component, {"documents_written": 0, "tokens": 0}
    )

    # === Mobility v1
    level_v1_stats = stats["mobility_v1"].setdefault(
        doc_mobility_v1, {"documents_written": 0, "tokens": 0, "sources": {}}
    )
    level_v1_source_stats = level_v1_stats["sources"].setdefault(
        doc_corpus, {"documents_written": 0, "tokens": 0, "genres": {}}
    )
    genre_v1_stats = level_v1_source_stats["genres"].setdefault(
        doc_genre, {"documents_written": 0, "tokens": 0}
    )

    # === Mobility v2
    level_v2_stats = stats["mobility_v2"].setdefault(
        doc_mobility_v2, {"documents_written": 0, "tokens": 0, "sources": {}}
    )
    level_v2_source_stats = level_v2_stats["sources"].setdefault(
        doc_corpus, {"documents_written": 0, "tokens": 0, "genres": {}}
    )
    genre_v2_stats = level_v2_source_stats["genres"].setdefault(
        doc_genre, {"documents_written": 0, "tokens": 0}
    )

    # Increment document pointers
    increment(cluster_stats, "documents_written")
    increment(cluster_source_stats, "documents_written")
    increment(component_stats, "documents_written")

    increment(level_v1_stats, "documents_written")
    increment(level_v1_source_stats, "documents_written")
    increment(genre_v1_stats, "documents_written")

    increment(level_v2_stats, "documents_written")
    increment(level_v2_source_stats, "documents_written")
    increment(genre_v2_stats, "documents_written")

    # Increment token pointers
    increment(cluster_stats, "tokens", token_count)
    increment(cluster_source_stats, "tokens", token_count)
    increment(component_stats, "tokens", token_count)

    increment(level_v1_stats, "tokens", token_count)
    increment(level_v1_source_stats, "tokens", token_count)
    increment(genre_v1_stats, "tokens", token_count)

    increment(level_v2_stats, "tokens", token_count)
    increment(level_v2_source_stats, "tokens", token_count)
    increment(genre_v2_stats, "tokens", token_count)

    return
