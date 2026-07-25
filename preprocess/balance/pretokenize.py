import subprocess
from pathlib import Path


def tokenize_source(documents_glob: str, destination: Path, config: dict):
    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "dolma",
        "tokens",
        "--documents",
        documents_glob,
        "--destination",
        destination,
        "--tokenizer.name_or_path",
        config["tokenizer"]["name"],
        "--tokenizer.eos_token_id",
        config["tokenizer"]["eos_token_id"],
        "--tokenizer.pad_token_id",
        config["tokenizer"]["pad_token_id"],
        "--dtype",
        "uint32",
        "--process",
        8,
    ]
    subprocess.run(cmd, check=True)
    return


def run(output_files: dict, output_dir: Path, config: dict):
    base_dir = output_dir / "pretokenized/"
    for cluster_id, documents_glob in output_files.items():
        destination = base_dir / f"cluster_{cluster_id}"
        tokenize_source(documents_glob, destination, config)
    return
