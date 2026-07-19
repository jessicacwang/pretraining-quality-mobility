import argparse
from preprocess.manifest import PreprocessManifest
from utils import load_config
import gzip
import preprocess.balance.index as index 
import preprocess.balance.budget as budget
import preprocess.balance.partition as partition
import preprocess.balance.materialize as materialize
import preprocess.balance.pretokenize as pretokenize
import random
from pathlib import Path 

def main(args):
    # Set random seed
    random.seed(args.random_seed)

    # Load config
    config = load_config(args.config_path)
    strategy = config["strategy"]
    validation_pct = config["validation_pct"]
    source_allocation = config["source_allocation_pct"]

    # Prepare output dir
    output_dir = Path(f"{args.output_dir}/{strategy}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # load Manifest and start step
    manifest = PreprocessManifest(f"{args.output_dir}/manifest.json")

    manifest.start_step("balance", args.notes)
    manifest.set_args("balance", vars(args))

    output_files = {
        "1": f"{args.output_dir}/{strategy}/cluster_1_{strategy}.jsonl.gz",
        "2": f"{args.output_dir}/{strategy}/cluster_2_{strategy}.jsonl.gz",
        "3": f"{args.output_dir}/{strategy}/cluster_3_{strategy}.jsonl.gz",
        "4": f"{args.output_dir}/{strategy}/cluster_4_{strategy}.jsonl.gz",
        "validation": f"{args.output_dir}/{strategy}/validation_{strategy}.jsonl.gz",
    }

    manifest.set_output_files("balance", output_files)

     # Create all output file handles
    writers = {}
    for key, path in output_files.items():
        writers[key] = gzip.open(path, "wt")

    try:
        # Build id -> tokens index, cluster -> source -> id catalog
        id_to_tokens, all_cluster_ids = index.build(config)

        # Compute budget
        token_budget = budget.compute(manifest["steps"]["enrich"], validation_pct=validation_pct, source_allocation_pct=source_allocation)
        manifest.set_balance_targets(token_budget, source_allocation, validation_pct)

        # Map doc IDs to output paths, building stats
        id_to_output_key, stats = partition.run(id_to_tokens, all_cluster_ids, token_budget)
        
        # Materialize sampled JSONL data
        materialize.write(config, id_to_output_key, writers)

        # Pretokenize data for olmix
        pretokenize.run(output_files, config)

        # Register completed step in manifest
        manifest.end_step("balance")
        manifest.set_balance_stats(stats=stats)
    except Exception as e:
        manifest.fail_step("balance", str(e))
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
    # TODO: add argument --strategy to toggle between sampling strategies (balanced, full)
    args = parser.parse_args()
    main(args)
