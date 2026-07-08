"""Defines specific preprocess functions for the PreprocessManifest class"""
from manifest import BaseManifest
from typing import Dict, Any

class PreprocessManifest(BaseManifest):
    def __init__(self, path):
        super().__init__(path)

    # ==========================================================================
    # Unify stats
    # ==========================================================================
    def set_unify_stats(self, corpus_name: str, stats: Dict[str, Any]):
        step = self.data["steps"].setdefault("unify", {})
        step.setdefault("corpora", {})[corpus_name] = stats
        return
    # ==========================================================================
    # Enrich step methods
    # ==========================================================================

    # ==========================================================================
    # Balance step methods
    # ==========================================================================