import numpy as np
from typing import List


def compute_lookups(all_token_counts: List[int]):
    # sort all_token_counts
    sorted_token_counts = sorted(all_token_counts)
    n = len(sorted_token_counts)
    unique_token_counts = np.unique(sorted_token_counts)

    # compute percentile lookups
    # Rightmost insertion position
    ranks = np.searchsorted(sorted_token_counts, unique_token_counts, side="right")

    # Compute percentiles
    percentiles = (ranks / n) * 100

    # Build lookup
    percentile_lookup = dict(zip(unique_token_counts, percentiles))
    return percentile_lookup
