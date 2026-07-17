# CLMS Thesis

This repository contains the code for the experiments composing my CLMS thesis, 
across 2 main experiments and 4-6 evaluation metrics.

No output `.jsonl.gz` is committed to the remote repository.

# Prerequisites
This code is designed to run on the UW Hyak computing cluster. The virtual 
environment is managed with Conda, and can be set up by running `setup.slurm` or 
`setup.sh` locally. 

# Experiments
All experiments are run from the repository root since all code is written 
using absolute package imports. 

# Data Manifests
To track the data volumes manipulated by each package in this repository, the 
Python class `BaseManifest` is defined. Package-specific stats are defined in 
subclasses `PreprocessManifest` and `FilterManifest`. These classes primarily 
handle the writing of `manifest.json` files and basic file reading. 

## Preprocessing: Unifying, Enriching, and Balancing Data
The `preprocess` package contains 3 main sub-packages: `unify`, `enrich`, and 
`balance`. The package structure is as follows:
```
.
├── __init__.py
├── balance
│   ├── __init__.py
│   ├── __main__.py
│   ├── budget.py
│   ├── index.py
│   ├── materialize.py
│   ├── partition.py
│   ├── pretokenize.py
│   └── temp.py
├── enrich
│   ├── __init__.py
│   ├── __main__.py
│   ├── features
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   ├── buckets.py
│   │   ├── clustering.py
│   │   ├── percentiles.py
│   │   ├── README.md
│   │   └── tokens.py
│   └── metadata.py
├── manifest.py
├── unify
│   ├── __init__.py
│   ├── __main__.py
│   ├── adapters
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   ├── base.py
│   │   ├── glowbe.py
│   │   ├── ice.py
│   │   ├── lince.py
│   │   └── README.md
│   └── normalize
│       ├── __init__.py
│       ├── __pycache__
│       ├── component.py
│       ├── corpus.py
│       ├── ice.py
│       ├── README.md
│       ├── tag_coverage.py
│       └── tag_shapes.py
└── utils.py
```
<!-- TODO: remove out-dated/overly detailed sub-package info -->
<!-- TODO: break down the 3 sub-package executable steps -->
### Unify
This step handles unification of LEU sources to JSONL data. Exact details on 
ICE normalization is described in `preprocess/unify/normalize/README.md`, as are 
details for LEU source adaptation to JSONL in `preporcess/unify/adapters/README.md`. 

This step is submitted a SLURM job as Hyak:
```cmd
sbatch 1-unify.slurm
```

Under `output/preprocess`, this results in:
- the initial `manifest.json`
- `leu_data.jsonl.gz`; each line contains fields `id` and `text`
- `metadata_sources.jsonl.gz` which maps `id` to source-derived metadata (ex: CMI scores, genre, modality...)

### Enrich
This step handles enrichment of the data with features relevant to both audit experiments: the localized English typological cluster ID and token properties 
(e.g., counts and percentiles). Documents are tokenized using the `allenai/dolma2` 
tokenizer. More details on features can be found in `preprocess/enrich/features/README.md`. 

The job is submitted as below:
```cmd
sbatch 2-enrich.slurm
```

Under `output/preprocess`, 
- the existing `manifest.json` is updated with `steps.enrich` 
- `metadata_enriched.jsonl.gz` is materialized to map `id` to cluster and token metadata.

### Balance
<!-- TODO: mention dolma dependency and pipx -->
This step handles the cluster "balancing" relevant to Audit 2a specifically by creating data samples, stratified by typological cluster ID, with equal 
token volume allocation between clusters, as well as proportional token volume allocation of ICE and GloWbe data *within* cluster samples. 

For exact details on the modules defined in the `preprocess.balance` sub-package, see `preprocess/balance/README.md`. At a high level:
1. Token budget targets are computed using the provided configuration and sampling strategy under `config/preprocess/balance.json` 
2. Documents are shuffled using `random.shuffle` and a random seed
3. Document IDs, partitioned by cluster, are accumulated until token budgets are met
4. Sampled document IDs are materialized under `output/preprocess/<strategy>`
5. The `dolma` CLI is used to pre-tokenize outputs for Audit 2.  

The following job is submitted to Hyak:
```cmd
sbatch 3-balance.slurm
```

By default, the `balanced` strategy is used (as described). The alternative 
strategy is `full` which document IDs are partitioned but no strict sampling 
budget is set. 

Under `output/preprocess`
- the existing `manifest.json` is updated with `steps.balance` 
- a `<strategy>` folder containining `cluster_<ID>.jsonl.gz` 
- `<strategy>/tokens/cluster_<ID>` folders containing sharded `*.npy` pre-tokenized data
### Outputs
In summary:
```
.
└── output
    └── preprocess
        ├── manifest.json               # updated at each step
        ├── leu_data.jsonl.gz           # created by unify
        ├── metadata_source.jsonl.gz    # created by unify
        ├── metadata_enriched.jsonl.gz  # created by enrich
        └── balanced                    # created by balance
            ├── cluster_1.jsonl.gz
            ├── cluster_2.jsonl.gz
            ├── cluster_3.jsonl.gz
            ├── cluster_4.jsonl.gz
            └── tokens
                ├── cluster_1
                │   ├── part-00.npy
                │   └── ...
                ├── cluster_2
                ├── cluster_3
                └── cluster_4
```

## Audit 1: Algorithmic Data Filters
<!-- TODO: audit is run by bash script, defined by filter/__main__ -->
<!-- filter/__main__ calls filter.pipeline and filter.audit -->
<!-- TODO: data must be pre-sharded using the splti command in bash script -->
### Pipeline
### Audit
<!-- TODO: describe relationship with evaluation and separate responsibilities -->
<!-- The `filter` module executes the algorithmic data filters used to create FineWeb 
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
are written to `output/filter/manifest.json`.  -->

### Outputs
<!-- TODO: add brief description of outputs -->

## Audit 2: Data Mixing Algorithms
<!-- TODO: describe configs created for the audit -->
<!-- The `mix` module executes an end-to-end data mixing algorithm based on data 
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
``` -->
# Evaluation
<!-- Separate responsibilities: eval modules should compute metric results, jupyter notebooks will visualize only  -->
## Stage 1
### Pointwise Mutual Information
<!-- TODO: specify relevant section of FilterManifest object -->
PMI values can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter/manifest.json`. 

They will be visualized with horizontal bar graphs with `plotly`. 

### Typological Cluster Retention
<!-- TODO: specify relevant section of FilterManifest object -->
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
<!-- TODO: leave hook for KS distance and Shannon entropy calculation -->
### Change in Token Distribution
The initial token distribution as recorded in `output/preprocess/manifest.json` 
for the balanced cluster data is accessed, as well as the relevant `.json` 
files under `output/mix/leu_optimization`. Shannon entropy of each token 
distribution is computed with `scipy`, as will the KS test between each pair of 
token distributions.

<!-- TODO: leave hooks for non-essential eval metrics -->
## Qualitative Analysis (TBD)
### Corpus Statistics
### Source/Genre Retention
