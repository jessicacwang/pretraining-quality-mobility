from pathlib import Path
from typing import Dict, Tuple, Any
from filter.audit.utils import get_counts_from_included


def update_stats(
    cumul_stats: Dict[str, Any],
    id_to_metadata: Dict[str, Tuple],
    output_dir: Path,
):
    included_stats, excluded_stats = get_counts_from_included(
        id_to_metadata, output_dir
    )
    cumul_stats["included"] = included_stats
    cumul_stats["excluded"] = excluded_stats
    return
