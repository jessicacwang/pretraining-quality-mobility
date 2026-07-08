"""Defines a BaseManifest object class to track run state + data provenance"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from collections import Counter, defaultdict


# ==========================================================================
# Helpers
# ==========================================================================
def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_git_commit() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return None


def get_slurm_job() -> Optional[str]:
    return os.environ.get("SLURM_JOB_ID")

    # ==========================================================================
    # Superclass
    # ==========================================================================


class BaseManifest:
    def __init__(self, path: str):
        self.path = Path(path)
        self.data = self._load()
        return

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"commit": get_git_commit(), "created_at": now(), "steps": {}}

    def save(self) -> None:
        """Save to a temp file, then rename to ensure safe completion"""
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                self.data, indent=2, default=self._json_serializer, sort_keys=True
            )
        )
        tmp.replace(self.path)
        return

    def _json_serializer(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, (Counter, defaultdict)):
            return dict(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    # ==========================================================================
    # Step execution
    # ==========================================================================
    def start_step(self, step: str, notes: Optional[str] = None) -> None:
        # initialize the current step field
        self.data["steps"][step] = {}

        self.data["steps"][step].update(
            {
                "started_at": now(),
                "status": "running",
                "_notes": notes,
                "execution": {"slurm_job_id": get_slurm_job()},
            }
        )
        return

    def end_step(self, step: str) -> None:
        s = self.data["steps"][step]
        s["completed_at"] = now()
        s["status"] = "success"

        s["total_seconds"] = (
            datetime.fromisoformat(s["completed_at"])
            - datetime.fromisoformat(s["started_at"])
        ).total_seconds()
        return

    def fail_step(self, step: str, error: str) -> None:
        s = self.data["steps"][step]
        s["completed_at"] = now()
        s["status"] = "failed"
        s["error"] = error

    # ==========================================================================
    # Step configuration
    # ==========================================================================

    def set_args(self, step: str, args: Dict[str, Any]):
        self.data["steps"].setdefault(step, {})
        self.data["steps"][step]["args"] = args
        return

    def set_output_files(self, step: str, files: Dict[str, str]):
        self.data["steps"].setdefault(step, {})
        self.data["steps"][step]["output_files"] = files
        return
