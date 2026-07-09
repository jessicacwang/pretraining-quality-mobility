"""Derive metadata fields not inherent to source datasets (token_count, token_percentile, etc.) and update output/preprocess/metadata.jsonl.gz"""
from preprocess.manifest import PreprocessManifest
from typing import Dict

def percentile_lookup(token_counts: list[int]) -> Dict[int, int]:
    # count length of token counts
    # initialize 
    return

def bucket_lookup(token_count: int) -> str:
    # 0-64
    # 64-128
    # 128-256
    # 256-512
    # 512-1024
    # 1024-2048
    # 2048+
    return

def main():
    # load Manifest
    manifest = PreprocessManifest()

    # initialize list of token counts
    all_token_counts = list()

    # load leu_data
    # open metadata_source
    # open metadata_enriched_tmp
    
    # ================ Derive fields local to the document itself ================
    # for document, source_metadata in zip(leu_data, metadata_source)
        # ==== Clustering
        # Assign cluster ID using preprocess/config/enrich.json
        # ==== Tokens
        # tokenize
        # record token count and accumulate
        # assign length bucket
        # TODO: duplicates?
        # ==== Gopher quality criteria
        # n_words = number of words 
        # avg_n_words = mean word length
        # ellipsis count
        # hashtag (#) count
        # non_alpha_words = words with alphabetic characters
        # n_stopwords = intersection with datatrove.pipeline.filters.gopher_quality_filter STOPWORDS
        # ==== C4 quality criteria
        # n_sentences = number of sentences
        # n_line_words = number of words per line
        # TODO: Javascript, lorem ipsum, curly bracket, cookies and terms of use keywords?
        # ==== FineWeb criteria 
        # n_punct = number of punctuation marks from datatrove.utils.text TERMINAL_PUNCTUATION
        # TODO: line length
        # write enriched doc to metadata_enriched_tmp
    
    # write total token count to manifest

    # sort all_token_counts
    # compute percentile lookups

    # open metadata_enriched_final

     # ================ Derive global fields ================
     # for document in metata_enriched_tmp
        # percentile = token_percentiles[document["token_count"]]
        # set token_percentile field
        # write document to final metadata
    # register run completion in manifest
    # save manifest
    return

if __name__ == "__main__":
    main()
