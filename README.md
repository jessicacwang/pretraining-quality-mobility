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

## Data Manifests
To track the data volumes manipulated by each package in this repository, the 
Python class `BaseManifest` is defined. Package-specific stats are defined in 
subclasses `PreprocessManifest` and `FilterManifest`. These classes primarily 
handle the writing of `manifest.json` files and basic file reading. 

## Preprocessing: Unifying, Enriching, and Balancing Data
The `preprocess` package contains 3 main sub-packages: `unify`, `enrich`, and 
`balance`. The package structure is as follows:
```
.
├── preprocess
│   ├── __init__.py
│   ├── balance/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── budget.py
│   │   ├── index.py
│   │   ├── materialize.py
│   │   ├── partition.py
│   │   ├── pretokenize.py
│   │   └── README.md
│   ├── enrich/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── features/
│   │   │   ├── __init__.py
│   │   │   ├── buckets.py
│   │   │   ├── clustering.py
│   │   │   ├── percentiles.py
│   │   │   ├── tokens.py
│   │   │   └── README.md
│   │   └── metadata.py
│   ├── manifest.py
│   ├── unify/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── glowbe.py
│   │   │   ├── ice.py
│   │   │   ├── lince.py
│   │   │   └── README.md
│   │   └── normalize/
│   │       ├── __init__.py
│   │       ├── component.py
│   │       ├── corpus.py
│   │       ├── ice.py
│   │       ├── tag_coverage.py
│   │       ├── tag_shapes.py
│   │       └── README.md
│   └── utils.py
├── 1-unify.slurm
├── 2-enrich.slurm
└── 3-balance.slurm
```
### Unify (`preprocess.unify`)
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

### Enrich (`preprocess.enrich`)
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

### Balance (`preprocess.balance`)
This step handles the cluster "balancing" relevant to Audit 2a specifically by creating data samples, stratified by typological cluster ID, with equal 
token volume allocation between clusters, as well as proportional token volume allocation of ICE and GloWbe data *within* cluster samples. 

For exact details on the modules defined in the `preprocess.balance` sub-package, see `preprocess/balance/README.md`. At a high level:
1. Token budget targets are computed using the provided configuration and sampling strategy under `config/preprocess/balance.json` 
2. Documents are shuffled using `random.shuffle` and a random seed
3. Document IDs, partitioned by cluster, are accumulated until token budgets are met
4. Sampled document IDs are materialized under `output/preprocess/<strategy>`
5. The `dolma tokens` CLI is used to pre-tokenize outputs for Audit 2.  

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
This experiment is to audit the sensitivity of algorithmic data filters to localized English usage. It is executed with `4-filter.sh`. The directory structure relevant to `filter` package is as follows:
```
.
├── filter/
│   ├── trove/
│   │   ├── id_logger.py
│   │   └── pipeline.py
│   ├── audit/
│   │   └── stats.py
│   ├── __main__.py
│   └── manifest.py 
└── 4-filter.sh
```
### Pipeline (`filter.trove`)
This sub-package provides the logic to instantiate and execute a `datatrove` pipeline executor according to `config/filter/pipeline.json` that reproduces all the filters used to create FineWeb. It also defines a class `DocumentIdLogger` as a subclass of `datatrove`'s `PipelineStep` to log all the document IDs that are forwarded by an algorithm in the filter pipeline. 

Tracking document IDs allows us to compute progressive retention metrics (see [Evaluation](#evaluation) below). The excluded documents and included document IDs are stored under `output/filter` (see below).

### Audit (`filter.audit`)
This subpackage provides the logic to accumulate two types of statistics as data for a `FilterManifest` object:
1. **progressive**: document volumes tracked as the pipeline progresses, w.r.t. cluster/source/component or genre
2. **cumulative**: document volumes tracked after the entire pipeline completes, w.r.t. cluster/source/component or genre. These results are directly compared to `steps.unify` document volumes from `output/preprocess/manifest.json`

The output of this subpackage is materialized as `output/filter/manifest.json`.

### Shell (`4-filter.sh`)
This script consists of 5 main steps:

1. Splits `leu_data.jsonl.gz` into `N` shards based on `config/filter/pipeline.json` 
2. Executes `filter.trove.pipeline`; on Hyak this instantiates a `SlurmPipelineExecutor` object which schedules its own array of jobs
3. Polls the slurm queue until no more jobs are running
3. Validates that all pipeline jobs succeeded 
4. Validates that `stats.json` exists
5. Execute `filter.audit.stats` to collect results

### Outputs
```
.
└── output
    ├── preprocess/
    ├── ...
    └── filter/
        ├── manifest.json
        ├── excluded/ 
        │   ├── 1_lang_id/
        │   │   └── 0000.jsonl.gz
        │   ├── 2_gopher_repetition/
        │   │   └── 0000.jsonl.gz
        │   ├── 3_gopher_quality/
        │   │   └── 0000.jsonl.gz
        │   ├── 4_c4_quality/
        │   │   └── 0000.jsonl.gz
        │   └── 5_fineweb_quality/
        │       └── 0000.jsonl.gz
        └── included/
            ├── after_1_langid.txt
            ├── after_2_gopher_repetition.txt
            ├── after_3_gopher_quality.txt
            ├── after_4_c4_quality.txt
            └── after_5_fineweb_quality.txt
```
<!-- ## \[WIP\] Audit 2: Data Mixing Algorithms
This experiment is to audit the sensitivity of data mixing algorithms to localized English usage by measuring the change in cluster/domain token volumes when optimizing data mixtures for HellaSwag.

To do so, the `mix` package is designed based on data mixing laws and other recommendations published for Olmix. It is responsible for the following:

1. Compute Dirichlet distribution priors
2. Generate candidate data mixtures
3. Launch a proxy swarm
4. Collect BPB loss for mixing targets
5. Fit a log-linear regression model
6. Report an optimized mix

All steps besides step 3 (launching a proxy swarm) and step 4 (collecting BPB loss metrics on mixing targets) will leverage the `olmix` CLI by defining YAML configs for data sources ([example](https://github.com/allenai/olmix/blob/main/configs/examples/generate/example.yaml)) and baseline launch mixtures ([example](https://github.com/allenai/olmix/blob/main/configs/examples/launch/data_proportions/mix_baseline.yaml)). 

### \[WIP\] Launching a Proxy Model Swarm

### \[WIP\] Collecting BPB Loss
There are 4 data mixing target "tasks" to be pursued jointly and independently:
1. LEU validation set (next token prediction)
2. HellaSwag
3. Trans-EnV HellaSwag (New Zealand English as proxy for Cluster 2)
4. Trans-EnV HellaSwag (Bahamian English as proxy for Cluster 4) -->

<!-- TODO: compute BPB: https://medium.com/@dip.patel.ict/bits-per-byte-bpb-a-tokenizer-agnostic-way-to-measure-llms-25dfed3f41af -->

### \[WIP\] Outputs
<!-- 
# Evaluation -->
<!-- Separate responsibilities: eval modules should compute metric results, jupyter notebooks will visualize only  -->
<!-- Python modules within `eval` package will transform `manifest.json` results into `plotly` friendly shapes. Finally, `eval/filter_audit.ipynb` and `eval/mix_audit.ipynb` will visualize graphs and transform data into LaTeX tables as needed.

| Audit | Metric | Visualization | Description |
| --- | --- | --- | --- |
| 1 |  PMI | bar graph | pointwise mutual information |
| 1 | RR | Sankey | retention rate |
| 1 | LRP | table | log-retention penalty |
| 1 | PR | table | Pearson's *r* |
| 2 | KSD | table | Kolmogorov-Smirnov Distance |
| 2 | SE | table | Shannon entropy 
## Audit 1
### Pointwise Mutual Information -->
<!-- TODO: specify relevant section of FilterManifest object -->
<!-- PMI values can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter/manifest.json`. 

```
PMI(x, y) = log_2 P(x, y) / (P(x) * P(y))
```
where `y` is always the probability that a document is dropped, and `x` is the probability of a document feature (dialect cluster, source, or genre).

They will be visualized with horizontal bar graphs with `plotly`.  -->

<!-- ### Retention Rates
Retention rates can be computed from the relevant fields of 
`output/preprocess/manifest.json` and `output/filter/manifest.json`. 
```
RR(i) = D_i / D_{i-1}
```
Where `D_i` is the number of document after step `i` in the filtering pipeline. 
Retention rates will be visualized with a `plotly` Sankey diagram. Additionally, 
log-retention penalties will be computed. 

### Correlation Analysis
Analysis will be performed by calculating Pearson's coefficient `r` and the 
coefficient of determination `R_2` using `scipy`. The the rows of 
`metadata.jsonl.gz` that correspond to Cluster 5 will be compared to the final 
results of `output/filter/5-fineweb_quality_filter/5-data.jsonl.gz` (tentatively) 
to produce pairs of (CMI, exclude/include) values.  -->
## Audit 2
<!-- TODO: leave hook for KS distance and Shannon entropy calculation -->
<!-- ### Kolgomorov-Smirnov Distance
This measure will be computed by using the `scipy` KS test metric against the initial domain weights and the 4 resultant optimized domain weights.  -->

<!-- ### Shannon entropy
This measure will be computed using `scipy` against all 5 domain weights as a qualitative metric for the amount of change caused by data mixing.  -->

<!-- TODO: leave hooks for non-essential eval metrics -->
<!-- ### Corpus Statistics (TBD) -->