from typing import Dict 

from eval.features import aggregate_by_features
from eval.subsets import SubsetSpec
from eval.retention.sankey_style import SankeyBuilder

def build_subset_sankey(stages: Dict, spec: SubsetSpec) -> Dict:
    b = SankeyBuilder()
    stage_items = list(stages.items())

    prev_node_key: Dict[str, str] = {}

    for i, (_, stage) in enumerate(stage_items):
        stage_name = stage["full_name"]

        included_by_val = aggregate_by_features(
            stage["included"]["records"], spec.feature_names, spec.record_filter
        )
        excluded_by_val = aggregate_by_features(
            stage["excluded"]["records"], spec.feature_names, spec.record_filter
        )
        all_values = set(included_by_val) | set(excluded_by_val)

        if i == 0: # First stage 
            for v in all_values:
                total = included_by_val.get(v, 0) + excluded_by_val.get(v, 0)
                if total <= 0:
                    continue # Guardrail in case data is funky
                key = f"s0::{v}"
                label = f"{v or spec.title} ({stage_name} in)"
                b.node(key, label, value=v or "total")
                prev_node_key[v] = key

        next_node_key: Dict[str, str] = {}
        for v, src_key in list(prev_node_key.items()):
            inc = included_by_val.get(v, 0)
            exc = excluded_by_val.get(v, 0)

            if exc > 0:
                excl_key = f"excl::{i}::{v}"
                b.node(excl_key, label="", value=v or "total")
                b.link(src_key, excl_key, exc, label=f"{v or spec.title} excluded @ {stage_name}")

            if inc > 0:
                next_key = f"s{i + 1}::{v}"
                label = f"{v or spec.title} ({stage_name} out)"
                b.node(next_key, label, value=v or "total")
                b.link(src_key, next_key, inc, label=f"{v or spec.title} @ {stage_name}")
                next_node_key[v] = next_key 

        # Link the next stage
        prev_node_key = next_node_key
    return b.to_dict()

def build_all_sankeys(stages: Dict, subset) -> Dict[str, Dict]:
    return {
        spec.key: build_subset_sankey(stages, spec)
        for spec in subset
    }