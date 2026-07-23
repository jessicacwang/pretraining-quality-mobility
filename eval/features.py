from typing import Callable, Dict, Iterable, Optional, Sequence 

FEATURE_POSITIONS = {"cluster": 0, "source": 1, "component": 2, "genre": 3}

NORMALIZE_FEATURES = {"component", "genre"}

def normalize_value(feature_name: str, value: str) -> str:
    if feature_name in NORMALIZE_FEATURES and "-" in value:
        return value.split("-")[0]
    return value

RecordFilter = Callable[[Sequence[str]], bool]

def restrict_to(feature_name: str, allowed_values: Iterable[str]) -> RecordFilter:
    position = FEATURE_POSITIONS[feature_name]
    allowed = set(allowed_values)

    def _filter(parts: Sequence[str]) -> bool:
        return parts[position] in allowed 

    return _filter

def exclude_nulls(feature_name: str) -> RecordFilter:
    position = FEATURE_POSITIONS[feature_name]

    def _filter(parts: Sequence[str]) -> bool:
        return parts[position] != "null"

    return _filter

def combine_filters(*filters: Optional[RecordFilter]) -> RecordFilter:
    active = [f for f in filters if f is not None]

    def _filter(parts: Sequence[str]) -> bool:
        return all(f(parts) for f in active)

    return _filter

def aggregate_by_feature(records: Dict[str, int], feature_name: str) -> Dict[str, int]:
    return aggregate_by_features(records, [feature_name])

def aggregate_by_features(
        records: Dict[str, int],
        feature_names: Sequence[str],
        record_filter: Optional[RecordFilter] = None,
) -> Dict[str, int]:
    out: Dict[str, int] = {}

    for key, count in records.items():
        parts = key.split("|")

        if record_filter and not record_filter(parts):
            continue 

        vals = tuple(
            normalize_value(f, parts[FEATURE_POSITIONS[f]]) for f in feature_names
        )

        label = " / ".join(vals)

        out[label] = out.get(label, 0) + count 

    return out 