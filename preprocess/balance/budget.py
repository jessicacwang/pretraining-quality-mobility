from typing import Dict, List, Tuple, Optional


def compute(
    enrich_stats: Dict,
    validation_pct: int,
    source_allocation_pct: Optional[Dict[str, int]],
) -> Dict:

    # Record limiting factor: Cluster 1's ICE tokens
    limiting_factor = enrich_stats["clusters"]["1"]["sources"]["ice"]["tokens"]

    # Limiting factor determines validation target
    validation_target = (validation_pct) * limiting_factor

    if source_allocation_pct:  # Only assigned to value if strategy is balanced
        # Validation target determines ICE target
        ice_target = (1 - validation_pct) * limiting_factor
        # Compute total cluster sample size and GloWbe target
        cluster_target = ice_target // source_allocation_pct["ice"]
        glowbe_target = cluster_target - ice_target
        total_target = 4 * cluster_target
    else:
        cluster_target = None
        glowbe_target = None
        ice_target = None
        total_target = None

    return {
        "total": total_target,
        "per_cluster": {
            "total": cluster_target,
            "glowbe": glowbe_target,
            "ice": ice_target,
        },
        "validation_size_per_source": validation_target,
    }


def accumulate(
    records: List[str], id_to_tokens: Dict[str, int], token_budget: Optional[int]
) -> Tuple[List, int]:
    accumulated_ids = []
    total_tokens = 0

    # Treat None as infinite budget
    budget = float("inf") if token_budget is None else token_budget

    while records:
        doc_id = records[-1]  # Peek at the next record
        token_count = id_to_tokens[doc_id]

        # If budget is not infinite, check whether it's been exceeded
        if total_tokens + token_count > budget:
            over = (total_tokens + token_count) - token_budget
            under = token_budget - total_tokens
            if over >= under:
                break

        # Pop and accumulate
        records.pop()
        accumulated_ids.append(doc_id)  # Put it back
        total_tokens += token_count
    return accumulated_ids, total_tokens
