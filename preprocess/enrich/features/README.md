# Enriched Features

This library contains modules that extract features of interest for characterizing LEU sources.

## Clustering
This module pulls from the provided enrich stage config to map corpus-component attributes to cluster IDs. 

## Tokens
This module uses the `dolma2-tokenizer` to pre-compute token counts, which 
will be used for the succeeding balance stage of preprocessing. It also tracks whether documents have been truncated.

## Buckets
This module returns a generalized size bucket category dependent on a document's token length.

## Percentiles
This module returns a percentile rank, computed globally across all unique token lengths, regardless of LEU source. 