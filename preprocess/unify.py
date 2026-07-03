"""Loads extracted and adapted LEU documents, activate Manifest tracking and writes to output/preprocess"""
from preprocess.adapters.glowbe import GloWbeAdapter
from preprocess.adapters.ice import ICEAdapter
from preprocess.adapters.lince import LinCEAdapter
from preprocess.manifest import PreprocessManifest

def main():
    # load Manifest, initializing if it doesn't exist
    manifest = PreprocessManifest()

    # open leu_data writer
    # open metadata writer

    # initialize adapters
    #TODO: add root_path and file pattern params
    adapters = [GloWbeAdapter(), ICEAdapter(), LinCEAdapter()]

    # loop through source adapters
        # register corpus in manifest

        # loop over documents
            # write text record
            # write metdata record
            # update document counters
        
        # record validation counts
    
    # register run completion in manifest
    # save manifest
    return

if __name__ == "__main__":
    #TODO: load unify.json 
    main()
