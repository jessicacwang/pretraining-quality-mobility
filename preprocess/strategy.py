from preprocess.manifest import PreprocessManifest
from typing import Dict, List, Tuple


def compute_token_budget(
    manifest: PreprocessManifest,
    validation_pct: int,
    source_allocation_pct: Dict[str, int],
) -> Dict:
    enrich_stats = manifest["steps"]["enrich"]

    # Record limiting factor: Cluster 1's ICE tokens
    limiting_factor = enrich_stats["clusters"]["1"]["sources"]["ice"]["tokens"]

    # Limiting factor determines validation target and ICE target
    validation_target = (validation_pct) * limiting_factor
    ice_target = (1 - validation_pct) * limiting_factor

    # Compute total cluster sample size and GloWbe target
    cluster_target = ice_target // source_allocation_pct["ice"]
    glowbe_target = cluster_target - ice_target
    return {
        "total": 4 * cluster_target,
        "per_cluster": {
            "total": cluster_target,
            "glowbe": glowbe_target,
            "ice": ice_target,
        },
        "validation_size_per_source": validation_target,
    }


def accumulate_until_budget(
    records: List[str], id_to_tokens: Dict[str, int], token_budget: int
) -> Tuple[List, int]:
    accumulated_ids = []
    total_tokens = 0

    while records and total_tokens < token_budget:
        doc_id = records.pop()
        token_count = id_to_tokens[doc_id]

        # Check if adding this doc takes us over or under the budget
        over = (total_tokens + token_count) - token_budget
        under = token_budget - total_tokens

        if over > 0 and over >= under:
            records.append(doc_id)  # Put it back
            break
        accumulated_ids.append(doc_id)
        total_tokens += token_count
    return accumulated_ids, total_tokens
