"""Samples from full LEU data to produce a uniformly distributed initial data mixture in output/preprocess/balanced"""
from collections import defaultdict
from preprocess.manifest import PreprocessManifest

def main():
    # load Manifest
    manifest = PreprocessManifest()

    # load token budget from arguments

    # initialize token_targets dict
    token_targets = dict()

    # compute token budget per cluster
        # compute token budget per source
    # update manifest with token_targets 

    # load metadata
    
    # group leu_data by metadata cluster + source - maybe defaultdict?
    
    # initialize cluster to list of IDs
    selected_ids = defaultdict(list)

    # initialize cluster to file writers
    writers = dict()

    # loop over clusters
        # loop over source subset
            # initialize token count for the source
            
            # shuffle documents

            # loop over documents
                # append doc to selected_ids[cluster]
                # update token count
                # break loop if token_target[cluster][source] has been met
        
            # write selected docs to cluster writer
            # write actual tokens and len(selected) to manifest
    
    # load leu_data
    # loop over leu_data
        # loop over cluster keys
            # if document ID is in selected_ids[cluster]:
                # write the document to the cluster output
    return

if __name__ == "__main__":
    main()
