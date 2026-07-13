from utils import load_config
from filter.manifest import FilterManifest
from datatrove.executor.slurm import SlurmPipelineExecutor
from datatrove.pipeline.filters import (
    C4QualityFilter,
    FineWebQualityFilter,
    GopherQualityFilter,
    GopherRepetitionFilter,
    LanguageFilter,
)
from datatrove.pipeline.readers import JsonlReader
from datatrove.pipeline.writers.jsonl import JsonlWriter
import argparse

def main(args):
    # Load config
    config = load_config(args.config_path)

    executor = SlurmPipelineExecutor(
    job_name=config["job_name"],
    pipeline=[
            JsonlReader(
                data_folder=config["data_folder"],
                glob_pattern=config["glob_pattern"]
            ),
            LanguageFilter(
                exclusion_writer=JsonlWriter(
                    f"{args.output_dir}/excluded/1_langid_excluded.jsonl.gz"
                )
            ),
            GopherRepetitionFilter(
                exclusion_writer=JsonlWriter(
                    f"{args.output_dir}/excluded/2_gopher_repetition_excluded.jsonl.gz"
                )
            ),
            GopherQualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{args.output_dir}/excluded/3_gopher_quality_excluded.jsonl.gz"
                )
            ),
            C4QualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{args.output_dir}/excluded/4_c4_quality_excluded.jsonl.gz"
                )
            ),
            FineWebQualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{args.output_dir}/excluded/5_fineweb_quality_excluded.jsonl.gz"
                )
            ),
            JsonlWriter(
                args.output_dir
            )
        ],
        env_command=config["env_command"],
        tasks=40,
        time="10:00:00",
        logging_dir=f"log/fineweb_filter",
        slurm_logs_folder=f"log/fineweb_filter/slurm_logs",
        mem_per_cpu_gb=2,
        sbatch_args=config["sbatch_args"],
        partition="compute"
    )
    executor.run()

    # TODO: review logging_dir/stats for filter-level totals
    # TODO: stream metadata_enriched to store id -> (cluster, source, component) details
    # TODO: stream metadata_source to store id -> (genre, modality, non_english) wherever exists
    # TODO: update manifest stats: filter -> cluster -> source -> component -> genre

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter")
    parser.add_argument("--config_path", default="filter/config/pipeline.json")
    args = parser.parse_args()
    main(args)