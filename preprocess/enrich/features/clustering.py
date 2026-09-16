from typing import Dict, Any

def get_id(cluster_config: Dict[str, Any], leu_doc: Dict[str, str], source_metadata: Dict[str, str]) -> str:
    doc_id = leu_doc.get("id")
    corpus = doc_id.split("_")[0]
    component =     source_metadata["component"]
    mapping = cluster_config["corpora"][corpus]

    if mapping.get("default", None):
        return mapping["default"], corpus, component
    return mapping["components"][component], corpus, component
