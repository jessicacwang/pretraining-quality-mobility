import argparse
import random
from pathlib import Path
import gzip

from preprocess.manifest import PreprocessManifest
import preprocess.balance.index as index
import preprocess.balance.budget as budget
import preprocess.balance.partition as partition
import preprocess.balance.materialize as materialize
import preprocess.balance.pretokenize as pretokenize
from utils import load_config


def main(args):
    # Set random seed
    random.seed(args.random_seed)

    # Load config
    config = load_config(args.config_path)
    validation_pct = config["validation_pct"]
    # Only register source allocation config if strategy is balanced
    if args.strategy == "balanced":
        source_allocation = config["source_allocation_pct"]
    else:
        source_allocation = None

    # Prepare output dir
    output_dir = Path(f"{args.output_dir}/{args.strategy}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # load Manifest and start step
    manifest = PreprocessManifest(f"{args.output_dir}/manifest.json")

    manifest.start_step(args.strategy, args.notes)
    manifest.set_args(args.strategy, vars(args))

    output_files = {
        "1": f"{args.output_dir}/{args.strategy}/cluster_1_{args.strategy}.jsonl.gz",
        "2": f"{args.output_dir}/{args.strategy}/cluster_2_{args.strategy}.jsonl.gz",
        "3": f"{args.output_dir}/{args.strategy}/cluster_3_{args.strategy}.jsonl.gz",
        "4": f"{args.output_dir}/{args.strategy}/cluster_4_{args.strategy}.jsonl.gz",
        "validation": f"{args.output_dir}/{args.strategy}/validation_{args.strategy}.jsonl.gz",
    }

    # Assign an output path for Cluster 5 if using full data for data mixing
    if args.strategy == "full":
        output_files["5"] = (
            f"{args.output_dir}/{args.strategy}/cluster_5_{args.strategy}.jsonl.gz"
        )

    manifest.set_output_files(args.strategy, output_files)

    # Create all output file handles
    writers = {}
    for key, path in output_files.items():
        writers[key] = gzip.open(path, "wt")

    try:
        print("Building metadata index, cluster/source catalog...")
        # Build id -> tokens index, cluster -> source -> id catalog
        id_to_tokens, all_cluster_ids = index.build(
            args.metadata_enriched, args.strategy
        )

        # Compute budget
        print("Computing budget, setting targets...")
        token_budget = budget.compute(
            manifest["steps"]["enrich"],
            validation_pct=validation_pct,
            source_allocation_pct=source_allocation,
        )
        manifest.set_balance_targets(token_budget, source_allocation, validation_pct)

        print("Assigning doc IDs to output paths")
        # Map doc IDs to output paths, building stats
        id_to_output_key, stats = partition.run(
            id_to_tokens, all_cluster_ids, token_budget
        )

        print("Writing outputs...")
        # Materialize sampled JSONL data
        materialize.write(args.leu_data, id_to_output_key, writers)

        print("Pre-tokenizing JSONL data...")
        # Pretokenize data for olmix
        pretokenize.run(output_files, output_dir, config)

        # Register completed step in manifest
        manifest.end_step(args.strategy)
        manifest.set_balance_stats(stats=stats)
    except Exception as e:
        manifest.fail_step(args.strategy, str(e))
        raise
    finally:
        # Close output writers
        for writer in writers.values():
            writer.close()
        manifest.save()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", default="config/preprocess/balance.json")
    parser.add_argument("--output_dir", default="output/preprocess")
    parser.add_argument("--notes", default="")
    parser.add_argument("--random_seed", default=42)
    parser.add_argument("--leu_data", default="output/preprocess/leu_data.jsonl.gz")
    parser.add_argument(
        "--metadata_enriched", default="output/preprocess/metadata_enriched.jsonl.gz"
    )
    parser.add_argument("--strategy", choices=["balanced", "full"], default="balanced")
    args = parser.parse_args()
    main(args)
