from utils import load_config
from filter.manifest import FilterManifest
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
import argparse
import os
import socket
from typing import Dict, Union, Any, Tuple, List
from pathlib import Path
from datatrove.pipeline.base import PipelineStep

def detect_environment() -> str:
    hostname = socket.gethostname()
    if 'klone' in hostname.lower() or 'hyak' in hostname.lower():
        return 'hyak'
    return 'local'

def get_env_config(config, env):
    return config[env]

def build_pipline(config: Dict[str, Any], env_config: Dict[str, Any], output_dir: str) -> Tuple[List[PipelineStep], Path, Path]:
    output_path = f"{env_config["base_dir"]}/{output_dir}"
    excluded_path = f"{output_path}/excluded"
    log_path = f"{env_config["base_dir"]}/log/{config["job_name"]}"
    pipeline=[
            JsonlReader(
                data_folder=env_config["data_folder"],
                glob_pattern=env_config["glob_pattern"]
            ),
            LanguageFilter(
                exclusion_writer=JsonlWriter(
                    f"{excluded_path}/1_langid"
                )
            ),
            GopherRepetitionFilter(
                exclusion_writer=JsonlWriter(
                    f"{excluded_path}/2_gopher_repetition"
                )
            ),
            GopherQualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{excluded_path}/3_gopher_quality"
                )
            ),
            C4QualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{excluded_path}/4_c4_quality"
                )
            ),
            FineWebQualityFilter(
                exclusion_writer=JsonlWriter(
                    f"{excluded_path}/5_fineweb_quality"
                )
            ),
            JsonlWriter(
                output_path
            )
        ]
    return pipeline, output_path, log_path

def get_executor(env: str, config: Dict[str, Any], env_config: Dict[str, Any], pipeline: PipelineStep, log_path: str) -> Union[LocalPipelineExecutor, SlurmPipelineExecutor]:
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
            partition=env_config["partition"]
        )
    
    return LocalPipelineExecutor(
        pipeline=pipeline,
        workers=env_config["workers"],
        logging_dir=log_path
    )

def main(args):
    # Load config
    config = load_config(args.config_path)

    # Detect environment
    env = detect_environment()
    print(f" Detected environment: {env.upper()}")

    # Get environment configuration for executor
    env_config = get_env_config(config, env)

    # Build pipeline
    pipeline, output_path, log_path = build_pipline(config, env_config, args.output_dir)

    # Get executor
    executor = get_executor(env, config, env_config, pipeline, log_path)
    
    try:
        executor.run()
    except Exception as e:
        print(f"Failed: {e}")
        raise

    # TODO: review logging_dir/stats for filter-level totals
    # TODO: stream metadata_enriched to store id -> (cluster, source, component) details
    # TODO: stream metadata_source to store id -> (genre, modality, non_english) wherever exists
    # TODO: update manifest stats: filter -> cluster -> source -> component -> genre

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="output/filter")
    parser.add_argument("--config_path", default="filter/config/pipeline.json")
    parser.add_argument("--env", choices=["auto", "hyak", "local"], default="auto")
    args = parser.parse_args()
    main(args)