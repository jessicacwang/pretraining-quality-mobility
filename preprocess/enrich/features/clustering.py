from typing import Dict, Any

def get_id(cluster_config: Dict[str, Any], leu_doc: Dict[str, str], metadata_source: Dict[str, str]) -> str:
    doc_id = leu_doc.get("id")
    corpus = doc_id.split("_")[0]
    component = metadata_source["component"]
    mapping = cluster_config["corpora"][corpus]

    if mapping.get("default", None):
        return mapping["default"], corpus, component
    return mapping["components"][component], corpus, component
