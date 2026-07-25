"""Loads extracted and adapted LEU documents, activate Manifest tracking and writes to output/preprocess"""
import argparse
import gzip
import json
from pathlib import Path
from tqdm import tqdm 

from preprocess.unify.adapters.glowbe import GloWbeAdapter
from preprocess.unify.adapters.ice import ICEAdapter
from preprocess.unify.adapters.lince import LinCEAdapter
from preprocess.manifest import PreprocessManifest
from utils import load_config


def main(args):
    # Prepare output dir
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # load Manifest, initializing if it doesn't exist
    manifest = PreprocessManifest(f"{args.output_dir}/manifest.json")

    manifest.start_step("unify", args.notes)
    manifest.set_args("unify", vars(args))

    output_files = {
        "leu_data": f"{args.output_dir}/leu_data.jsonl.gz",
        "metadata": f"{args.output_dir}/metadata_source.jsonl.gz",
    }
    manifest.set_output_files("unify", output_files)

    # load unify config
    config = load_config(args.config_path)
    # open metadata writer

    # initialize adapters
    adapters = [
        LinCEAdapter(
            config["corpora"]["lince"]["root_path"],
            config["corpora"]["lince"]["file_pattern"],
        ),
        ICEAdapter(
            config["corpora"]["ice"]["root_path"],
            config["corpora"]["ice"]["file_pattern"],
            config["corpora"]["ice"]["tag_registry"],
        ),
        GloWbeAdapter(
            config["corpora"]["glowbe"]["root_path"],
            config["corpora"]["glowbe"]["file_pattern"],
        ),
    ]
    try:
        # open leu_data writer, open metadata writer
        with gzip.open(output_files["leu_data"], "wt") as leu_gz, gzip.open(
            output_files["metadata"], "wt"
        ) as meta_gz:

            for corpus_adapter in tqdm(adapters, desc="source adapters", position=0):
                # Prepare adapter
                print(f"\nProcessing {corpus_adapter.name}")
                corpus_adapter.prepare()

                try:
                    doc_count = 0
                    # loop over documents
                    for d in tqdm(corpus_adapter.iter_documents(), desc="source docs", position=1, leave=False):
                        # write text record
                        leu_gz.write(json.dumps({"id": d.id, "text": d.text}) + "\n")

                        # write metdata record
                        meta_gz.write(json.dumps({"id": d.id} | d.metadata) + "\n")

                        doc_count += 1
                        if doc_count % 10000 == 0:
                            print(f"    Processed {doc_count} documents...")

                    stats = corpus_adapter.get_stats()
                    manifest.set_unify_stats(corpus_adapter.name, stats)
                    print(
                        f"    Completed: {stats['documents_written']} written, "
                        f"    {sum(stats['documents_dropped'].values())} dropped"
                    )
                except Exception as e:
                    print(f"    [!!] Error processing {corpus_adapter.name}: {e}")
                    try:
                        stats = corpus_adapter.get_stats()
                        manifest.set_unify_stats(
                            corpus_adapter.name, {"error": str(e), **stats}
                        )
                    except:
                        pass
                    raise
                finally:
                    # cleanup adapter
                    corpus_adapter.cleanup()
            # register run completion in manifest
            manifest.end_step("unify")
            print(f"\n **UNIFY COMPLETE!** Output in {output_dir}")
    except Exception as e:
        manifest.fail_step("unify", str(e))
        print(f"\n**UNIFY FAILED:** {e}")
        raise
    finally:
        # save manifest
        manifest.save()

        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", default="config/preprocess/unify.json")
    parser.add_argument("--output_dir", default="output/preprocess")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    main(args)
