import argparse
from preprocess.normalize.corpus import CorpusNormalizer


def main():
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Reorganize ICE components as configured"
    )
    parser.add_argument(
        "--mapping",
        help="Path to mapping JSON file",
        default="preprocess/config/ice_dir_normalize.json",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Execute changes (default is dry run)"
    )

    args = parser.parse_args()

    # define a CorpusNormalizer
    reorganizer = CorpusNormalizer(mapping_file=args.mapping, dry_run=not args.execute)

    # Run the CorpusNormalizer
    reorganizer.run()
    return


if __name__ == "__main__":
    main()
