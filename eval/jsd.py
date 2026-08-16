from scipy.spatial import distance

# Load enriched metadata (token count, cluster_ID, locality, mobility)

# Loop over filter/*.jsonl.gz to tally up cumulative results
# Increment cluster x locality x mobility volume by token count

# Compare aggregated total metadata results (initial) to cumulative results
# distance.jensenshannon(initial, final, base=2) ** 2
