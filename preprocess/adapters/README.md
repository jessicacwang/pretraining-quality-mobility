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

In GloWbe documents, 10 words are obfuscated with the string "@ @ @ @ @ @ @ @ @ @" 
every 200 words. For this study, the sentences affected by obfuscation are 
removed by `clean_text()`. 

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
ICE documents represent generally acrolectal (more formal) registers of English 
in different English-speaking regions, but two annotation tags are of interest 
for this study: `foreign` and `indig`, which should surround foreign words (which 
excludes common borrowings) and indigenous words. Notably, different regional 
components may mark up the non-English code, e.g. `<foreign=French>` or `<indig=Maori>`,
but for the basic metadata these are all aggregated. Also, documents with component
values `ke` or `tz` may use the `<ea>` tag to mark indigenous words. The 
tagging of these documents was done completely by hand, some before the 21st 
century, so there are helper functions and regular expressions to accommodate 
human errors. The instances of these tags are returned by `extract_metadata()`.

Note as well that any tag can come in one of the following forms:
```python
#This tag applies to the entire span
(A) '<tag> these words are associated with this tag </tag>'

#This tag only applies to the following word
(B) '<tag/> word'
```
This class defines two main cleaning actions, resulting in four main outcomes:
```python
DROP FULL SPAN: 
    (A) '<tag> these words are associated with this tag </tag>' 
            ==> ''
DROP TAG ONLY:
    (A) '<tag> these words are associated with this tag </tag>' 
            ==> 'these words are associated with this tag'

DROP FULL SPAN:
(B) '<tag/> word' 
        ==> ''

DROP TAG ONLY:
(B) '<tag/> word' 
        ==> 'word'
```

There are 3 edge cases:
- the normative deletion tag form where the original text is included between angle brackets: `<-_{original_text}>` - in this case, the original text needs to be captured and preserved.
- the named entity marker `<@>` as used for the ICE-AUS component, where but the tag surrounds an anonymized name, e.g., `<@>constituencyname5</@>` or `<@>secondname2</@>`
- the standalone anonymized name tag `<name>`, as used exclusively in ICE-EA. It presents the same function as the `<@>` tag. 

The `ICEAdapter` class differs from its siblings in that it accepts an attribute `tag_registry` which provides 5 fields:
```json
{
    "treat_as_foreign": [],
    "treat_as_indig": [],
    "alter": {

    },
    "drop_tag_only": [
        ...
    ],
    "drop_full_span": [
        ...
    ]
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

LinCE documents with language identification labels are the only ones eligible 
to be included in this study because the labels allow us to compute CMI (also 
known as code-mixing index) values; this represents the amount of "switching" 
that speakers are doing between English or their other language. This is computed 
and returned by `extract_metadata()`. 