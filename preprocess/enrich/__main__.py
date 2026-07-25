"""Derive metadata fields not inherent to source datasets (token_count, token_percentile, etc.) and update output/preprocess/metadata.jsonl.gz"""
import argparse
from pathlib import Path
import gzip
import json
from tqdm import tqdm

from preprocess.manifest import PreprocessManifest
import preprocess.enrich.metadata as metadata
import preprocess.enrich.features.percentiles as percentiles
from utils import load_config


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

    try:
        # ========================== PASS 1: Local fields ==========================
        all_token_counts, stats, error_counts, truncated = metadata.build(args, config)
        # ========================== PASS 2: Global fields =========================
        # Pre-compute percentile lookups
        token_percentiles = percentiles.compute_lookups(all_token_counts)

        # open metadata_enriched_final (write) and enriched_tmp (read)
        with gzip.open("metadata_enriched_tmp", "rt") as tmp_gz, gzip.open(
            f"{output_dir}/metadata_enriched.jsonl.gz", "wt"
        ) as meta_gz:

            # for document in metata_enriched_tmp
            for line_num, tmp_line in enumerate(tqdm(tmp_gz, desc="tmp metadata"), 1):
                try:
                    tmp_doc = json.loads(tmp_line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    continue

                doc_percentile = token_percentiles[tmp_doc.get("token_count")]
                meta_gz.write(
                    json.dumps(tmp_doc | {"token_percentile": doc_percentile}) + "\n"
                )

        # === Update manifest
        manifest.set_enrich_stats(
            stats=stats,
            errors=dict(error_counts),
            truncated=truncated,
            cluster_descriptions=config["descriptions"],
        )
        manifest.end_step("enrich")
    except Exception as e:
        manifest.fail_step("enrich", str(e))
        raise
    finally:
        Path("metadata_enriched_tmp").unlink(missing_ok=True)
        manifest.save()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", default="config/preprocess/enrich.json")
    parser.add_argument("--output_dir", default="output/preprocess")
    parser.add_argument("--leu_data", default="output/preprocess/leu_data.jsonl.gz")
    parser.add_argument(
        "--metadata_source", default="output/preprocess/metadata_source.jsonl.gz"
    )
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    main(args)
