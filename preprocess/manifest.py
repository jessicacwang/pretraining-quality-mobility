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
    def set_enrich_stats(self, stats: Dict, errors: Dict, truncated: int, cluster_descriptions: Dict):
        step = self.data["steps"].setdefault("enrich", {})
        step["enrich_errors"] = errors
        step["documents_truncated"] = truncated

        clusters = {}
        for cluster_id, cluster_stats in stats.items():
            clusters[cluster_id] = {
                "description": cluster_descriptions.get(cluster_id, ""),
                **cluster_stats
            }

        step["clusters"] = clusters
        return 
    # ==========================================================================
    # Enrich step methods
    # ==========================================================================

    # ==========================================================================
    # Balance step methods
    # ==========================================================================
