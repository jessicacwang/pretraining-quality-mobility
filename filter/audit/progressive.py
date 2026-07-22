from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from filter.audit.utils import get_counts_from_excluded


def update_stats(
    prog_stats: Dict[str, Any],
    algo_stats: Dict[str, Any],
    id_to_metadata: Dict[str, Tuple],
    excluded_dir: Path,
    algo_key: str,
    now_excluded: set = set(),
):

    # Filter datatrove stats for desired items
    target_algo_stats = {
        k: v
        for k, v in algo_stats["stats"].items()
        if k.startswith("dropped") or k == "total" or k == "forwarded"
    }

    # Initialize the current algorithm's progressive stats
    prog_stats[algo_key] = {"full_name": algo_stats["name"]}

    # Update the progressive stats with the total number of dropped/forwarded
    prog_stats[algo_key] |= target_algo_stats

    # Update the progressive stats with subtotals by bucket (cluster, source, component, genre)
    print(" -------- counting metadata instances")
    result = get_counts_from_excluded(id_to_metadata, excluded_dir, now_excluded)
    print(" -------- finished counting metadata")
    prog_stats[algo_key]["excluded"] = result["excluded_counts"]
    prog_stats[algo_key]["included"] = result["included_counts"]
    return result["now_excluded"]
