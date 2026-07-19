# Corpus Normalization

This library defines Python classes and scripts to adapt ICE components to the 
unified JSONL format. 

### `preprocess.unify.normalize.ice`
This module takes a config file `config/preprocess/ice_dir_normalize.json` and 
normalizes the source corpora file patterns into a uniform directory tree of 
depth 2. It relies on 2 main subclasses:

#### `CorpusNormalizer`
This class handles directory and file normalization at the entire corpus level 
by instantiating the proper `ComponentNormalizer` objects and logging changes,
errors, and warnings. 

#### `ComponentNormalizer`
This class handles directory and file normalization at the regional component 
level by defining specific iteration and parsing functions for the 'default' case 
or specialized cases where the regional component is organized uniquely (ex: 
ICE-EA, ICE-GB, and ICE-NG). While most files' genre information is normalized 
to the standard ICE 3-character code, exceptions are made for ICE-EA and ICE-NG 
files to retain as much data as possible.

### `preprocess.unify.normalize.tag_shapes`
Now that the ICE corpus has been normalized in its directory tree structure, the 
text within the documents need to be normalized. The first step to doing so is 
to verify what annotation patterns exist across regional components. This enables 
us to determine how those tags will be cleaned in the LEU unificiation process. 

To do so, first perform a maximally inclusive search for possible tag shapes and redirect to a plaintext file:
```cmd
cd data/ice
grep -Eho "<[^>]+>" */* | sort | uniq -c | sort -rn > tag_count_inventory.txt
```

This plaintext file is the only required input to the module:
```cmd
python -m preprocess.unify.normalize.tag_shapes --file tag_count_inventory
```

The console results can also be redirected to a file for better visibility:
```cmd
python -m preprocess.unify.normalize.tag_shapes --file tag_count_inventory > tag_shapes.txt
```

### `preprocess.unify.normalize.tag_coverage`
This module predicts the well-formedness and fit of regular expressions to the tag inventory. It tests whether any tag in the inventory is matched by more than one regular expression and estimates the number of tags that are 'hit' by the proposed set of regular expressions. To use it, prepare a plaintext file with one regular expression on each line.
```cmd
python -m preprocess.unify.normalize.tag_coverage --regex <name of file containing candidate regex> --tags tag_count_inventory.txt
``` 
Testing with this module enabled me to create a set of 101 regular expressions that fits >99.95% of annotation tags without overlap, which I can map to cleaning actions in `preprocess.unify.adapters.ice`