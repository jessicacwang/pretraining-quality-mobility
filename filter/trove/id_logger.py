from datatrove.pipeline.base import PipelineStep
from datatrove.data import Document
from typing import Generator
from pathlib import Path


class DocumentIdLogger(PipelineStep):
    type = "🪵 LOGGER"
    name = "Local English Usage IDs"

    def __init__(self, stage_name: str, output_path: str):
        super().__init__()
        self.stage_name = stage_name
        self.log_file = Path(f"{output_path}/id_logs/after_{stage_name}_ids.txt")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def run(
        self, data: Generator[Document, None, None], rank: int = 0, world_size: int = 1
    ) -> Generator[Document, None, None]:
        # Use a lock or per-rank file to avoid conflicts in parallel execution
        log_path = f"{self.log_file}.rank_{rank}" if world_size > 1 else self.log_file

        with open(log_path, "w") as f:
            for doc in data:
                # Log the ID of every document that passes through this step
                self.stat_update(f"forwarded_by_{self.stage_name}")
                f.write(f"{doc.id}\n")
                yield doc
