# CLMS Thesis

This repository contains the code for the experiments composing my CLMS thesis, across 2 main experiments and 6 evaluation metrics.

No `.jsonl.gz` is committed to the remote repository.

# Prerequisites
This code is designed to run on the UW Hyak computing cluster. 

# Experiments
## Stage 0: Unifying, Clustering, and Balancing Data

The `preprocess` module handles the unification, clustering and re-balancing of 
existing datasets for the following stages. Directory structure is as follows:
```
.
└── preprocess/
    ├── config/
    │   └── cluster_config.json             # Cluster definitions
    ├── 0-unify.slurm                       # Step 0.0 
    ├── 1-cluster.slurm                     # Step 0.1
    ├── 2-balance.slurm                     # Step 0.2
    ├── balance.py                          # Called by 2-balance.slurm
    ├── cluster.py                          # Called by 1-cluster.slurm 
    ├── unify.py                            # Called by 0-unify.slurm
    └── convert_to_jsonl/                   # Called by unify.py
        ├── utils.py
        ├── glowbe/
        │   └── main.py
        ├── ice/
        │   └── main.py
        └── lince/
            └── main.py
```

This stage requires filepaths for ICE and GloWbe corpora to be configured in the 
environment. First, `convert_to_jsonl` submodules for each of the source corpora 
convert the data into JSONL. Three primary fields are shared by all submodules 
are:
- `id`: `"<corpus>_<source_hash>"` to be unambiguous
- `text`: plain text without annotations or markup tags
- `token_count`: the number of tokens in `text` using `AutoTokenizer`

Each of the `convert_to_jsonl` submodules can be tested individually by running:
```cmd
python -m preprocess.convert_to_jsonl.<source>
```

All submodules are called by `unify.py` as the first step of preprocessing. By 
default, this script runs everything to produce `full_data.jsonl.gz` and 
`metadata.jsonl.gz` but can be run to 'backfill'/update subsets of 
`full_data.jsonl.gz` by rewriting rows corresponding to a certain source with 
the argument `--source <source>`. Document and token counts are tracked in 
`manifest.json`. This initial parsing + cleaning is executed as below:
```cmd
sbatch preprocess/0-convert_to_jsonl.slurm
```

Next, the unified data is clustered by `cluster.py`. The `metadata.jsonl.gz` is 
updated by populating `cluster` field, using `cluster_config.json` to map 
relevant metadata fields to cluster IDs. `manifest.json` is similarly updated to 
include document and token counts per cluster, aggregating by source and by genre. 
```cmd
sbatch preprocess/1-cluster.slurm
```

Finally, the clustered data for Clusters 1-4 (ICE and GloWbe data) is rebalanced 
by `balance.py`, which samples from the full data to produce a uniform initial 
distribution between clusters as well as enforcing a uniform ratio of ICE and 
GloWbe tokens for the Data Mixing Audit. To do so, the script accesses 
`manifest.json` to compute exact token targets and samples from 
`full_data.jsonl.gz` until the targets are met for each cluster as well as a 
held-out validation set, approximately 2% of the total volume. The balanced 
results are written as separate `jsonl.gz` files, and `manifest.json` is updated.
```cmd
sbatch preprocess/2-balance.slurm
```

Note that the output will be written to the `output/preprocess` folder, of 
the following shape:
```
.
└── output/
    └── preprocess/
        ├── manifest.json       
        ├── metadata.jsonl.gz                   # secondary JSON fields
        ├── full_data.jsonl.gz                  # Created by 1-cluster.slurm
        └── balanced/                           # Created by 2-balance.slurm
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
`<filter>/<stage>_data.jsonl.gz`. The corresponding excluded documents are 
written to `<filter>/removed/<stage>_data.jsonl.gz`.  The document and token 
counts for included and excluded documents for each filtering stage are written 
to `output/filter/manifest.json`. 

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
`output/preprocess/manifest.json` and `output/filter.json`. 

They will be visualized with horizontal bar graphs with `plotly`. 

### Typological Cluster Retention
Retention rates can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter.json`. 

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
