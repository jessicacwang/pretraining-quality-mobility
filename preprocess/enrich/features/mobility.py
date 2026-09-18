from typing import Dict, Any


def get_level(
    level_config: Dict[str, Any],
    leu_doc: Dict[str, str],
    source_metadata: Dict[str, str],
) -> str:
    doc_id = leu_doc.get("id")
    corpus = doc_id.split("_")[0]
    genre = source_metadata.get("genre", "default").split("-")[0]
    mapping = level_config["corpora"][corpus]

    if mapping.get("default", None):
        return mapping["default"], mapping["default"], genre
    return mapping["genre"][genre]["v1"], mapping["genre"][genre]["v2"], genre
