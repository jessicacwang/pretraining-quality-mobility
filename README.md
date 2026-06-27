# CLMS Thesis

This repository contains the code for the experiments composing my CLMS thesis, 
across 2 main experiments and 4-6 evaluation metrics.

No `.jsonl.gz` is committed to the remote repository.

# Prerequisites
This code is designed to run on the UW Hyak computing cluster.

# Experiments
All experiments are run from the repository root since all code is written 
using absolute package imports. 
## Stage 0: Unifying, Enriching, and Balancing Data

The `preprocess` module handles the unification, clustering and re-balancing of 
existing datasets for the following stages. Directory structure is as follows:
```
.
└── preprocess/
    ├── config/
    │   ├── enrich.json
    │   ├── ice_reorganize.json
    │   └── ice_tag.json
    ├── adapters/
    │   ├── __init__.py
    │   ├── glowbe.py
    │   ├── ice.py
    │   ├── lince.py
    │   └── utils.py
    ├── reorganize/
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── component_reorganizer.py
    │   └── corpus_reorganizer.py
    ├── 1-unify.slurm
    ├── 2-enrich.slurm
    ├── 3-balance.slurm
    ├── balance.py
    ├── enrich.py
    ├── manifest.py
    └── unify.py
```

This stage requires filepaths for ICE and GloWbe corpora to be configured in the 
config JSON. First, ICE data has differing directory structure depending on the 
regional component; these are reorganized using a Python class in the interest 
of reproducibility:

```cmd
python -m preprocess.reorganize --execute
```
Once ICE components are uniformly organized, all source LEU corpora can be unified 
as JSONL data. To do so, the `adapters` submodules are written to adapt each source 
corpus to JSON-like formats. Three primary fields are shared by all submodules, along 
with source-specific secondary fields (not listed):
- `id`: `"<corpus>_<source_hash>"` to be unambiguous
- `text`: plain text without annotations or markup tags

Each of the `adapters` submodules can be tested individually by running:
```cmd
python -m preprocess.adapters.<source>
```

The first proper step of preprocessing is unify the results of each LEU adapter 
and write the results. By default, the script writes the three primary fields to 
`leu_data.jsonl.gz` and the source-specific secondary fields to `metadata.jsonl.gz`. 
Document and token counts are tracked in `manifest.json`. This initial parsing + 
cleaning is executed as below:
```cmd
sbatch 1-unify.slurm
```

Next, the unified data is enriched; the `metadata.jsonl.gz` is updated by populating 
a `cluster` field, using `cluster_config.json` to map relevant secondary fields 
to cluster IDs, calculating token counts/percentiles, and tracking the occurrences 
of penalized text features (ex: non-alphanumeric characters, repetitions). 
`manifest.json` is similarly updated to include average counts per cluster/source/component/genre. 
```cmd
sbatch 2-enrich.slurm
```

Finally, the enriched data for Clusters 1-4 (ICE and GloWbe data) is rebalanced 
such that the full data is sampled to produce a uniform initial distribution 
between clusters and to enforce a uniform ratio of ICE and GloWbe tokens 
for the Data Mixing Audit. To do so, the script accesses `manifest.json` to 
compute exact token targets and samples from `leu_data.jsonl.gz` until the targets 
are met for each cluster as well as a held-out validation set, approximately 2% 
of the total volume. The balanced results are written as separate `jsonl.gz` files
for each cluster, and `manifest.json` is updated.
```cmd
sbatch 3-balance.slurm
```

Note that the output will be written to the `output/preprocess` folder, of 
the following shape:
```
.
└── output/
    └── preprocess/
        ├── manifest.json       
        ├── metadata.jsonl.gz                   # secondary JSON fields
        ├── leu_data.jsonl.gz                  # Created by 2-cluster.slurm
        └── balanced/                           # Created by 3-balance.slurm
            ├── cluster_1_balanced.jsonl.gz
            ├── cluster_2_balanced.jsonl.gz
            ├── cluster_3_balanced.jsonl.gz
            ├── cluster_4_balanced.jsonl.gz
            └── validation.jsonl.gz
```
More specifically, this stage results in 2 metadata files, and 6 data files 
(1 full, 5 balanced).

## Stage 1: Auditing Algorithmic Data Filters

The `filter` module executes the algorithmic data filters used to create FineWeb 
and tracks the inclusion and exclusion of every document after each of the five 
filters. This stage is executed as SLURM batch jobs, one for each cluster:
```cmd
sbatch filter/run.slurm
```
The output will be written to the `output/filter` directory. Full output filepaths 
are abbreviated below since this stage will result in 5 x 2 + 1 = 11 distinct 
files in the following shape:
```
.
└── output/
    ├── preprocess/
    │   └── ...
    └── filter/
        ├── manifest.json
        ├── 1-langid_included.jsonl.gz
        ├── 2-gopher-repetition_included.jsonl.gz
        ├── 3-gopher-quality_included.jsonl.gz
        ├── 4-c4-quality_included.jsonl.gz
        ├── 5-fineweb-quality_included.jsonl.gz
        └── excluded/
            ├── 1-langid_excluded.jsonl.gz
            ├── 2-gopher-repetition_excluded.jsonl.gz
            ├── 3-gopher-quality_excluded.jsonl.gz
            ├── 4-c4-quality_excluded.jsonl.gz
            └── 5-fineweb-quality_excluded.jsonl.gz
```

For each filtering stage, the documents included after the filter are written to 
`output/filter/<stage>_included.jsonl.gz`. The corresponding excluded documents 
are written to `output/filter/removed/<stage>_excluded.jsonl.gz`.  The document 
and token counts for included and excluded documents for each filtering stage 
are written to `output/filter/manifest.json`. 

## Stage 2: Auditing Data Mixing Algorithms
The `mix` module executes an end-to-end data mixing algorithm based on data 
mixing laws and other recommendations published for Olmix. 

As of now, I plan to use `olmix` to
1. Compute Dirichlet distribution priors
2. Generate data mixtures
3. Launch a proxy swarm
4. Train a regression model
5. Report an optimized mix

The outputs of each step will be recorded in the `output/mix` folder:
```
.
└── output/
    ├── preprocess/
    │   └── ...
    ├── filter/
    │   └── ...
    └── mix/
        ├── leu_priors.yaml
        ├── leu_variants/
        │   └── ...
        ├── leu_swarm/
        │   ├── ratios.csv
        │   └── metrics.csv
        └── leu_optimization/
            ├── config.json
            ├── interaction_matrix.png
            ├── <metric>_optimal.json
            ├── opt_avg_all_metrics_*_optimal.json
            └── ...
```
# Evaluation

## Stage 1
### Pointwise Mutual Information
PMI values can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter/manifest.json`. 

They will be visualized with horizontal bar graphs with `plotly`. 

### Typological Cluster Retention
Retention rates can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter/manifest.json`. 

Retention rates will be visualized with a `plotly` Sankey diagram. Additionally, 
log-retention penalties will be computed. 

### Correlation Analysis
Analysis will be performed by calculating Pearson's coefficient `r` and the 
coefficient of determination `R_2` using `scipy`. The the rows of 
`metadata.jsonl.gz` that correspond to Cluster 5 will be compared to the final 
results of `output/filter/5-fineweb_quality_filter/5-data.jsonl.gz` (tentatively) 
to produce pairs of (CMI, exclude/include) values. 
## Stage 2
### Change in Token Distribution
The initial token distribution as recorded in `output/preprocess/manifest.json` 
for the balanced cluster data is accessed, as well as the relevant `.json` 
files under `output/mix/leu_optimization`. Shannon entropy of each token 
distribution is computed with `scipy`, as will the KS test between each pair of 
token distributions.
## Qualitative Analysis (TBD)
### Corpus Statistics
### Source/Genre Retention
