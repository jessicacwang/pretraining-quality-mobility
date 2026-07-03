# Corpus Adapters

This library defines Python classes to adapt LEU sources to JSONL format with basic metadata from the source material. Some attributes are inferred from the source data file names; others are inferred from the document material itself. Metadata like `token_count`, `token_percentile` are populated by `preprocess.enrich` module.

The `BaseAdapter` class defines the main entry point, `iter_documents()` and 
basic attributes for source-level validation: `self.ids_observed` and `self.empty_text_count`. 

## GloWbe
The `GloWbeAdapter` class is responsible for adapting GloWbe texts. Each input 
GloWbe file contains all webpages for a single country; each document is a 
single line. The adapter parses each line and yields a `UnifiedDocument` with 
the following metadata dictionary:
```python
metadata = {
    ## Inferred from file name
    "component": <country code>,
    "source_filename": <file name>,
    "genre": <blog or general, inferred from file name>,
    ## Inferred from document material
    "glowbe_doc_id": <doc ID from first 11 characters of each line>,
    "original": <original text>
    "obfuscated": <number of obfuscation strings>
}
```

## ICE
The `ICEAdapter` class is repsonsible for adapting ICE texts. Each input ICE file corresponds to a single document. The adapter yields `UnifiedDocument` objects with the following metadata dictionary:
```python
metadata = {
    ## Inferred from file name
    "component": <country code from ICE component>,
    "source_filename": <file name>,
    "modality": <written or spoken, inferred from file name>,
    "genre": <ICE genre code from file name>,
    ## Inferred from document material
    "original": <original text>
    "foreign": <number of foreign tags>,
    "indigenous": <number of indig tags> 
}
```
## LinCE
The `LinCEAdapter` class is responsible for adapting LinCE data. Each input LinCE file coresponds to a data split (train/validation/test), but for the purpose of this study, any document with language identification labels is eligible to be selected (as a CMI score can be evaluated). Metadata looks like
```python
metadata = {
    ## Inferred from file name
    "component": <task name>,
    "source_filename": <source file name>,
    "non_english": <ISO 639 code>,
    "split": <train, validation, or test>,
    ## Inferred from document material
    "idx": <row number in original file>,
    "cmi": <CMI computed from "lid" column of original data>
}
```