from dataclasses import dataclass, field 
from typing import Dict, List, Optional, Sequence, Set

from eval.features import RecordFilter, aggregate_by_features, combine_filters, exclude_nulls, restrict_to

CLUSTERS_WITH_SOURCES_AND_GENRES = ["1", "2", "3", "4"]

SOURCES = ["glowbe", "ice", "lince"]

SOURCES_WITH_GENRE = ["glowbe", "ice"]

SOURCES_WITH_MULTIPLE_CLUSTERS = ["glowbe", "ice"]

@dataclass
class SubsetSpec:
    key: str # stable identifier, used in filenames and JSON keys
    title: str # human readable
    feature_names: Sequence[str] # which feature(s) to aggregate by
    record_filter: Optional[RecordFilter] = field(default=None)

def build_subsets() -> List[SubsetSpec]:
    subset: List[SubsetSpec] = [
        SubsetSpec("overall", "Overall volume", feature_names=[]),
        SubsetSpec("by_cluster", "By cluster", feature_names=["cluster"]),
        SubsetSpec("by_source", "By source", feature_names=["source"]),
        SubsetSpec(
            "by_cluster_source", "By cluster and source", 
            feature_names=["cluster", "source"]
        ),
        SubsetSpec(
            "by_cluster_component", "By cluster and component", 
            feature_names=["cluster", "component"]
        ),
        SubsetSpec(
            "by_cluster_genre", "By cluster and genre", 
            feature_names=["cluster", "genre"]
        ),
        SubsetSpec(
            "by_component_genre", "By component and genre", 
            feature_names=["component", "genre"]
        ),
        SubsetSpec(
            "by_genre", "By genre", 
            feature_names=["genre"],
            record_filter=exclude_nulls("genre")
        ),
        SubsetSpec(
            "by_component", "By component", 
            feature_names=["component"],
            record_filter=restrict_to("source", SOURCES_WITH_GENRE)
        ),
    ]

    for cluster in CLUSTERS_WITH_SOURCES_AND_GENRES:
        subset.append(
            SubsetSpec(
                key=f"by_source_in_cluster_{cluster}",
                title=f"By source, within cluster {cluster}",
                feature_names=["source"],
                record_filter=restrict_to("cluster", [cluster])
            )
        )
        subset.append(
            SubsetSpec(
                key=f"by_genre_in_cluster_{cluster}",
                title=f"By genre, within cluster {cluster}",
                feature_names=["genre"],
                record_filter=restrict_to("cluster", [cluster])
            )
        )

    for source in SOURCES:
        subset.append(
            SubsetSpec(
                key=f"by_component_in_{source}",
                title=f"By component, within source {source}",
                feature_names=["component"],
                record_filter=restrict_to("source", [source])
            )
        )

    for source in SOURCES_WITH_GENRE:
        subset.append(
            SubsetSpec(
                key=f"by_genre_in_{source}",
                title=f"By genre, within source {source}",
                feature_names=["genre"],
                record_filter=combine_filters(
                    restrict_to("source", [source]), exclude_nulls("genre")
                )
            )
        )

    for source in SOURCES_WITH_MULTIPLE_CLUSTERS:
        subset.append(
            SubsetSpec(
                key=f"by_cluster_in_{source}",
                title=f"By cluster, within source {source}",
                feature_names=["cluster"],
                record_filter=restrict_to("source", [source])
            )
        )

    return subset

def subset_value_universe(stages: Dict, spec: SubsetSpec) -> Set[str]:
    """
    Returns the set of distinct (and normalized) values that define a subset.
    Shared by eval.retention.plot_data and eval.colors
    """
    values: Set[str] = set()

    for _, stage in stages.items():
        values |= set(
            aggregate_by_features(stage["excluded"]["records"], spec.feature_names, spec.record_filter)
        )
        values |= set(
            aggregate_by_features(stage["included"]["records"], spec.feature_names, spec.record_filter)
        )
    return values