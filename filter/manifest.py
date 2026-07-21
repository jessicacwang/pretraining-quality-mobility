"""Defines specific preprocess functions for the FilterManifest class"""

from manifest import BaseManifest
from typing import Dict, Any


class FilterManifest(BaseManifest):
    def __init__(self, path):
        super().__init__(path)

    # ==========================================================================
    # Filter audit stats
    # ==========================================================================
    def set_audit_stats(self, stats: Dict[str, Any]):
        step = self.data["steps"].setdefault("filter", {})
        step |= stats
        return
