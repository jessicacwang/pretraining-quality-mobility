from collections import defaultdict
import random
from tqdm import tqdm

import preprocess.balance.budget as budget

def shuffle_ids(all_cluster_ids: defaultdict):
    # Shuffle all_cluster_ids values
    for _, cluster_records in tqdm(all_cluster_ids.items(), desc="shuffle cluster records"):
        random.shuffle(cluster_records["glowbe"])
        random.shuffle(cluster_records["ice"])
    return

def select_validation_ids(id_to_tokens: dict, all_cluster_ids: defaultdict, token_budget: dict, stats: dict):
    validation_ids = defaultdict(lambda: {"glowbe": set(), "ice": set(), "lince": set()})

    for cluster_id, records in all_cluster_ids.items():
        validation_glowbe, glowbe_subtotal = budget.accumulate(
            records["glowbe"], id_to_tokens, token_budget["validation_size_per_source"]
        )
        validation_ice, ice_subtotal = budget.accumulate(
            records["ice"], id_to_tokens, token_budget["validation_size_per_source"]
        )
        
        validation_lince, lince_subtotal = budget.accumulate(
            records["lince"], id_to_tokens, token_budget["validation_size_per_source"]
        )
        
        validation_ids[cluster_id]["glowbe"] |= set(validation_glowbe)
        validation_ids[cluster_id]["ice"] |= set(validation_ice)
        validation_ids[cluster_id]["lince"] |= set(validation_lince)

        docs_written = len(validation_glowbe) + len(validation_ice) + len(validation_lince)

        validation_subtotal = glowbe_subtotal + ice_subtotal + lince_subtotal
        curr_stats = stats["validation"]["clusters"].setdefault(
            cluster_id, {"documents_written": 0, "actual_token_count": {}}
        )
        curr_stats["documents_written"] += docs_written
        curr_stats["actual_token_count"] |= {
            "total": validation_subtotal,
            "glowbe": glowbe_subtotal,
            "ice": ice_subtotal,
            "lince": lince_subtotal
        }
    return validation_ids 

def select_ids_per_cluster_sample(id_to_tokens: dict, all_cluster_ids: defaultdict, token_budget: dict, stats: dict):
    per_cluster_ids = defaultdict(lambda: {"glowbe": set(), "ice": set(), "lince": set()})
    for cluster_id, records in tqdm(all_cluster_ids.items(), desc="accumulate cluster samples"):
        sampled_glowbe, glowbe_subtotal = budget.accumulate(
            records["glowbe"], id_to_tokens, token_budget["per_cluster"]["glowbe"]
        )
        sampled_ice, ice_subtotal = budget.accumulate(
            records["ice"], id_to_tokens, token_budget["per_cluster"]["ice"]
        )
        sampled_lince, lince_subtotal = budget.accumulate(
            records["lince"], id_to_tokens, None
        )
        
        per_cluster_ids[cluster_id]["glowbe"] |= set(sampled_glowbe)
        per_cluster_ids[cluster_id]["ice"] |= set(sampled_ice)
        per_cluster_ids[cluster_id]["lince"] |= set(sampled_lince)

        docs_written = len(sampled_glowbe) + len(sampled_ice) + len(sampled_lince)
        cluster_subtotal = glowbe_subtotal + ice_subtotal + lince_subtotal
        glowbe_pct = glowbe_subtotal / cluster_subtotal
        ice_pct = ice_subtotal / cluster_subtotal
        lince_pct = lince_subtotal / cluster_subtotal
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
            "lince": lince_subtotal
        }
        curr_stats["actual_token_pct"] |= {"glowbe": glowbe_pct, "ice": ice_pct, "lince": lince_pct}

    return

def build_id_to_output_cluster(per_cluster_ids: defaultdict, validation_ids: defaultdict):
    id_to_output_key = dict()

    for cluster_id, sources in tqdm(per_cluster_ids.items(), desc="cluster sample routing"):
        for source, ids in sources.items():
            for doc_id in ids:
                id_to_output_key[doc_id] = cluster_id
    for cluster_id, sources in tqdm(validation_ids.items(), desc="validation routing"):
        for source, ids in sources.items():
            for doc_id in ids:
                id_to_output_key[doc_id] = "validation"
    return id_to_output_key


def run(id_to_tokens: dict, all_cluster_ids: defaultdict, token_budget: dict):
    # Initialize storage
    stats = {"validation": {"clusters": {}}, "sampled": {"clusters": {}}}
    
    # Shuffle IDs for randomness
    shuffle_ids(all_cluster_ids)

    # Set aside validation set using budget["validation_size_per_source"] and strategy
    validation_ids = select_validation_ids(id_to_tokens, all_cluster_ids, token_budget, stats)
    
    # Accumulate doc IDs for each key in per_cluster_ids, for each source in budget["per_cluster"]
    per_cluster_ids = select_ids_per_cluster_sample(id_to_tokens, all_cluster_ids, token_budget, stats)

    # Map doc ID to output file
    id_to_output_key = build_id_to_output_cluster(per_cluster_ids, validation_ids)

    return id_to_output_key, stats