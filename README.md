# Probing Pretraining "Quality": Sociolinguistic Mobility as a Lens on Web Corpus Filters

This repository contains the code for the titular WaC-13 workshop paper.

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
