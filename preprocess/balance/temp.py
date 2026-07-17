"""Samples from full LEU data to produce a uniformly distributed initial data mixture in output/preprocess/balanced"""

from collections import defaultdict
from preprocess.manifest import PreprocessManifest
import argparse
from utils import load_config
from pathlib import Path
import gzip
import json
import random
from preprocess.strategy import compute_token_budget, accumulate_until_budget


def main(args):
    # Set random seed
    random.seed(args.random_seed)

    # Load config
    # TODO: restructure config to toggle between sampling strategies - update all config access below
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

    # compute token budget and update manifest with targets
    # TODO: implement a function for the full sampling strategy
    if strategy == "balanced":
        budget = compute_token_budget(manifest, validation_pct, source_allocation)
        manifest.set_balance_targets(budget, source_allocation, validation_pct)

    # Initialize storage
    stats = {"validation": {"clusters": {}}, "sampled": {"clusters": {}}}
    id_to_tokens = dict()
    all_cluster_ids = defaultdict(lambda: {"glowbe": list(), "ice": list()})
    validation_ids = defaultdict(lambda: {"glowbe": set(), "ice": set()})
    per_cluster_ids = defaultdict(lambda: {"glowbe": set(), "ice": set()})
    try:

        # =========================== ACCUMULATE IDs ===========================
        

        # Set aside validation set using budget["validation_size_per_source"] and each key in cluster_source_id_tokens
        for cluster_id, records in all_cluster_ids.items():
            validation_glowbe, glowbe_subtotal = accumulate_until_budget(
                records["glowbe"], id_to_tokens, budget["validation_size_per_source"]
            )
            validation_ice, ice_subtotal = accumulate_until_budget(
                records["ice"], id_to_tokens, budget["validation_size_per_source"]
            )

            validation_ids[cluster_id]["glowbe"] |= set(validation_glowbe)
            validation_ids[cluster_id]["ice"] |= set(validation_ice)

            docs_written = len(validation_glowbe) + len(validation_ice)
            validation_subtotal = glowbe_subtotal + ice_subtotal
            curr_stats = stats["validation"]["clusters"].setdefault(
                cluster_id, {"documents_written": 0, "actual_token_count": {}}
            )
            curr_stats["documents_written"] += docs_written
            curr_stats["actual_token_count"] |= {
                "total": validation_subtotal,
                "glowbe": glowbe_subtotal,
                "ice": ice_subtotal,
            }
        # Accumulate doc IDs for each key in per_cluster_ids, for each source in budget["per_cluster"]
        # TODO: when strategy == 'full', just update the stored IDs directly 
        for cluster_id, records in all_cluster_ids.items():
            sampled_glowbe, glowbe_subtotal = accumulate_until_budget(
                records["glowbe"], id_to_tokens, budget["per_cluster"]["glowbe"]
            )
            sampled_ice, ice_subtotal = accumulate_until_budget(
                records["ice"], id_to_tokens, budget["per_cluster"]["ice"]
            )

            per_cluster_ids[cluster_id]["glowbe"] |= set(sampled_glowbe)
            per_cluster_ids[cluster_id]["ice"] |= set(sampled_ice)

            docs_written = len(sampled_glowbe) + len(sampled_ice)
            cluster_subtotal = glowbe_subtotal + ice_subtotal
            glowbe_pct = glowbe_subtotal / cluster_subtotal
            ice_pct = ice_subtotal / cluster_subtotal
            curr_stats = stats["sampled"]["clusters"].setdefault(
                cluster_id,
                {
                    "documents_written": 0,
                    "actual_token_count": {},
                    "actual_token_pct": {},
                },
            )
            curr_stats["documents_written"] += docs_written
            curr_stats["actual_token_count"] |= {
                "total": cluster_subtotal,
                "glowbe": glowbe_subtotal,
                "ice": ice_subtotal,
            }
            curr_stats["actual_token_pct"] |= {"glowbe": glowbe_pct, "ice": ice_pct}

        # ========== PASS 2: Write LEU samples from accumulated IDs ============
        

        

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
