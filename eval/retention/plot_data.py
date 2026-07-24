import math 
from typing import Dict, List 

from eval.features import aggregate_by_features
from eval.subsets import SubsetSpec

def build_subset_series(stages: Dict, spec: SubsetSpec) -> List[Dict]:
    stage_items = list(stages.items())

    all_values = set()

    for _, stage in stage_items:
        all_values |= set(
            aggregate_by_features(stage["included"]["records"], spec.feature_names, spec.record_filter)
        )

        all_values |= set(
            aggregate_by_features(stage["excluded"]["records"], spec.feature_names, spec.record_filter)
        )

    if not all_values:
        all_values = {""}

    # Initialize cumulative LRP dict with zeros
    cumulative_lrp = {v: 0.0 for v in all_values}

    rows: List[Dict] = []

    for i, (_, stage) in enumerate(stage_items, start=1):
        stage_name = stage["full_name"]

        included_by_val = aggregate_by_features(
            stage["included"]["records"], spec.feature_names, spec.record_filter
        )
        excluded_by_val = aggregate_by_features(
            stage["excluded"]["records"], spec.feature_names, spec.record_filter
        )

        for v in sorted(all_values):
            inc = included_by_val.get(v, 0)
            exc = excluded_by_val.get(v, 0)
            total = inc + exc 

            if total > 0:
                retention = inc / total 
                lrp = -math.log(retention) if retention > 0 else float("nan")
                if not math.isnan(lrp):
                    cumulative_lrp[v] += lrp 
            else:
                # Value was fully excluded in earlier stage, so treat as zero
                retention = 0.0
                lrp = float("nan")

            rows.append(
                {
                    "value": v or "total",
                    "stage": i, 
                    "stage_name": stage_name,
                    "included": inc, 
                    "total": total, 
                    "retention": retention,
                    "lrp": lrp,
                    "cumulative_lrp": cumulative_lrp[v]
                }
            )
    return rows 

def build_all_series(stages: Dict, subset) -> Dict[str, List[Dict]]:
    return {
        spec.key: build_subset_series(stages, spec)
        for spec in subset
    }