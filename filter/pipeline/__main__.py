import argparse
from utils import load_config
from datatrove.executor.slurm import SlurmPipelineExecutor
from datatrove.executor.local import LocalPipelineExecutor
from datatrove.pipeline.filters import (
    C4QualityFilter,
    FineWebQualityFilter,
    GopherQualityFilter,
    GopherRepetitionFilter,
    LanguageFilter,
)
from datatrove.pipeline.readers import JsonlReader
from datatrove.pipeline.writers.jsonl import JsonlWriter
from typing import Dict, Union, Any, List
from datatrove.pipeline.base import PipelineStep
from filter.manifest import FilterManifest


def get_env_config(config, executor):
    return config[executor]


def build_pipline(env_config: Dict[str, Any]) -> List[PipelineStep]:

    excluded_path = f"{env_config["output_dir"]}/excluded"
    output_path = env_config["output_dir"]
    pipeline = [
        JsonlReader(
            data_folder=env_config["data_folder"],
            glob_pattern=env_config["glob_pattern"],
        ),
        LanguageFilter(exclusion_writer=JsonlWriter(f"{excluded_path}/1_langid")),
        GopherRepetitionFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/2_gopher_repetition")
        ),
        GopherQualityFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/3_gopher_quality")
        ),
        C4QualityFilter(exclusion_writer=JsonlWriter(f"{excluded_path}/4_c4_quality")),
        FineWebQualityFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/5_fineweb_quality")
        ),
        JsonlWriter(output_path),
    ]
    return pipeline


def get_executor(
    executor: str,
    config: Dict[str, Any],
    env_config: Dict[str, Any],
    pipeline: PipelineStep,
) -> Union[LocalPipelineExecutor, SlurmPipelineExecutor]:
    if executor == "slurm":
        return SlurmPipelineExecutor(
            job_name=config["job_name"],
            pipeline=pipeline,
            env_command=env_config["env_command"],
            workers=env_config["workers"],
            time=env_config["time"],
            logging_dir=env_config["log_dir"],
            slurm_logs_folder=f"{env_config["log_dir"]}/slurm",
            mem_per_cpu_gb=env_config["mem_per_cpu_gb"],
            sbatch_args=env_config["sbatch_args"],
            partition=env_config["partition"],
            tasks=env_config["tasks"],
            cpus_per_task=env_config["cpus_per_task"],
            tasks_per_job=env_config["tasks_per_job"],
        )

    return LocalPipelineExecutor(
        pipeline=pipeline,
        workers=env_config["workers"],
        logging_dir=env_config["log_dir"],
        tasks=4,
        skip_completed=False,
    )


def run(args):
    config = load_config(args.config)
    # Get environment configuration for executor

    env_config = get_env_config(config, args.executor)

    # Load manifest
    manifest = FilterManifest(f"{env_config["output_dir"]}/manifest.json")
    manifest.start_step("filter")

    # Build pipeline and set output
    pipeline = build_pipline(env_config)

    # Get executor and run
    executor = get_executor(args.executor, config, env_config, pipeline)
    executor.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--executor", choices=["slurm", "local"], default="slurm")
    parser.add_argument("--config", default="config/filter/pipeline.json")

    args = parser.parse_args()
    run(args)
