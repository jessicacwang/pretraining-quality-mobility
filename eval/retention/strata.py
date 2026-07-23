from dataclasses import dataclass, field 
from typing import List, Optional, Sequence 

from eval.features import RecordFilter, combine_filters, exclude_nulls, restrict_to

CLUSTERS_WITH_MULTIPLE_SOURCES = ["1", "2", "3", "4"]

SOURCES = ["glowbe", "ice", "lince"]

SOURCES_WITH_GENRE = ["glowbe", "ice"]

SOURCES_WITH_MULTIPLE_CLUSTERS = ["glowbe", "ice"]

@dataclass
class StratumSpec:
    key: str # stable identifier, used in filenames and JSON keys
    title: str # human readable
    feature_names: Sequence[str] # which feature(s) to aggregate by
    record_filter: Optional[RecordFilter] = field(default=None)

def build_strata() -> List[StratumSpec]:
    strata: List[StratumSpec] = [
        StratumSpec("overall", "Overall volume", feature_names=[]),
        StratumSpec("by_cluster", "By cluster", feature_names=["cluster"]),
        StratumSpec("by_source", "By source", feature_names=["source"])
    ]

    for cluster in CLUSTERS_WITH_MULTIPLE_SOURCES:
        strata.append(
            StratumSpec(
                key=f"by_source_in_cluster_{cluster}",
                title=f"By source, within cluster {cluster}",
                feature_names=["source"],
                record_filter=restrict_to("cluster", [cluster])
            )
        )

    for source in SOURCES:
        strata.append(
            StratumSpec(
                key="by_component_in_{source}",
                title=f"By component, within source {source}",
                feature_names=["component"],
                record_filter=restrict_to("source", [source])
            )
        )

    for source in SOURCES_WITH_GENRE:
        strata.append(
            StratumSpec(
                key="by_genre_in_{source}",
                title=f"By genre, within source {source}",
                feature_names=["genre"],
                record_filter=combine_filters(
                    restrict_to("source", [source]), exclude_nulls("genre")
                )
            )
        )

    for source in SOURCES_WITH_MULTIPLE_CLUSTERS:
        strata.append(
            StratumSpec(
                key=f"by_cluster_in_{source}",
                title=f"By cluster, within source {source}",
                feature_names=["cluster"],
                record_filter=restrict_to("source", [source])
            )
        )

    return strata