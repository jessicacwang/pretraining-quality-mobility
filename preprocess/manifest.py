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
    def set_enrich_stats(
        self, stats: Dict, errors: Dict, truncated: int, config: Dict
    ):
        step = self.data["steps"].setdefault("enrich", {})
        step["enrich_errors"] = errors
        step["documents_truncated"] = truncated

        clusters = {}
        levels_v1 = {}
        levels_v2 = {}
        for cluster_id, cluster_stats in stats["distribution"].items():
            clusters[cluster_id] = {
                "description": config["distribution"]["descriptions"].get(cluster_id, ""),
                **cluster_stats,
            }

        for mobility_level, level_stats in stats["mobility_v1"].items():
            levels_v1[mobility_level] = {
                "description": config["mobility"]["descriptions"].get(mobility_level, ""),
                **level_stats,
            }
        for mobility_level, level_stats in stats["mobility_v2"].items():
            levels_v2[mobility_level] = {
                "description": config["mobility"]["descriptions"].get(mobility_level, ""),
                **level_stats,
            }
        step["clusters"] = clusters
        step["levels_v1"] = levels_v1
        step["levels_v2"] = levels_v2
        return

    # ==========================================================================
    # Balance step methods
    # ==========================================================================
    def set_balance_targets(
        self, budget: Dict, source_allocation: Dict, validation_pct: int
    ):
        step = self.data["steps"].setdefault("balance", {})
        step["token_budget"] = budget
        step["validation_pct"] = (validation_pct,)
        step["source_allocation_pct"] = source_allocation
        return

    def set_balance_stats(self, stats: Dict):
        step = self.data["steps"].setdefault("balance", {})
        step |= stats
        return


if __name__ == "__main__":
    manifest = PreprocessManifest(f"output/preprocess/manifest.json")
    print(manifest["steps"]["enrich"].keys())
