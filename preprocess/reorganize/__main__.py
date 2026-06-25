import argparse
from preprocess.reorganize.corpus_reorganizer import CorpusReorganizer


def main():
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Reorganize ICE components as configured"
    )
    parser.add_argument(
        "--mapping",
        help="Path to mapping JSON file",
        default="preprocess/config/ice_reorganize.json",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Execute changes (default is dry run)"
    )

    args = parser.parse_args()

    # define a CorpusReorganizer
    reorganizer = CorpusReorganizer(mapping_file=args.mapping, dry_run=not args.execute)

    # Run the CorpusReorganizer
    reorganizer.run()
    return


if __name__ == "__main__":
    main()
