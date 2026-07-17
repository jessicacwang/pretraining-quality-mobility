from filter.manifest import FilterManifest
from filter.id_logger import DocumentIdLogger
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
import socket
from typing import Dict, Union, Any, Tuple, List
from pathlib import Path
from datatrove.pipeline.base import PipelineStep


def detect_environment() -> str:
    hostname = socket.gethostname()
    if "klone" in hostname.lower() or "hyak" in hostname.lower():
        return "hyak"
    return "local"


def get_env_config(config, env):
    return config[env]


def build_pipline(
    config: Dict[str, Any], env_config: Dict[str, Any], output_dir: str
) -> Tuple[List[PipelineStep], Path, Path]:
    output_path = f"{env_config["base_dir"]}/{output_dir}"
    excluded_path = f"{output_path}/excluded"
    log_path = f"{env_config["base_dir"]}/log/{config["job_name"]}"
    pipeline = [
        JsonlReader(
            data_folder=env_config["data_folder"],
            glob_pattern=env_config["glob_pattern"],
        ),
        LanguageFilter(exclusion_writer=JsonlWriter(f"{excluded_path}/1_langid")),
        DocumentIdLogger("1_langid", output_path),
        GopherRepetitionFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/2_gopher_repetition")
        ),
        DocumentIdLogger("2_gopher_repetition", output_path),
        GopherQualityFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/3_gopher_quality")
        ),
        DocumentIdLogger("3_gopher_quality", output_path),
        C4QualityFilter(exclusion_writer=JsonlWriter(f"{excluded_path}/4_c4_quality")),
        DocumentIdLogger("4_c4_quality", output_path),
        FineWebQualityFilter(
            exclusion_writer=JsonlWriter(f"{excluded_path}/5_fineweb_quality")
        ),
        DocumentIdLogger("5_fineweb_quality", output_path),
        JsonlWriter(output_path),
    ]
    return pipeline, output_path, log_path


def get_executor(
    env: str,
    config: Dict[str, Any],
    env_config: Dict[str, Any],
    pipeline: PipelineStep,
    log_path: str,
) -> Union[LocalPipelineExecutor, SlurmPipelineExecutor]:
    if env == "hyak":
        return SlurmPipelineExecutor(
            job_name=config["job_name"],
            pipeline=pipeline,
            env_command=env_config["env_command"],
            workers=env_config["workers"],
            time=env_config["time"],
            logging_dir=log_path,
            slurm_logs_folder=f"{log_path}/slurm_logs",
            mem_per_cpu_gb=env_config["mem_per_cpu_gb"],
            sbatch_args=env_config["sbatch_args"],
            partition=env_config["partition"],
            tasks=1,
        )

    return LocalPipelineExecutor(
        pipeline=pipeline,
        workers=env_config["workers"],
        logging_dir=log_path,
        # skip_completed=False,
    )


def run(config: Dict[str, Any], output_dir: str, manifest: FilterManifest):
    # Detect environment
    env = detect_environment()
    print(f" Detected environment: {env.upper()}")

    # Get environment configuration for executor
    env_config = get_env_config(config, env)

    # Build pipeline and set output
    pipeline, output_path, log_path = build_pipline(config, env_config, output_dir)

    manifest.set_output_files(
        "filter", {"output_data": output_path, "log_data": log_path}
    )

    # Get executor
    executor = get_executor(env, config, env_config, pipeline, log_path)
    executor.run()
    return output_path, log_path

if __name__ == "__main__":
    # TODO: this script will be run directly from login node
    pass