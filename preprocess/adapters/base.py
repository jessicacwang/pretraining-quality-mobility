"""Base class for CorpusAdapter objects: disover documents, construct IDs, extract metadata and prepare text"""
from pathlib import Path
import hashlib
from typing import Dict

class BaseAdapter:
    TARGET_ID_KEYS = []    
    def __init__(self, root_path: str, file_pattern: str):
        self.path = Path(root_path)
        self.file_pattern = file_pattern
        return
    
    def _iter_source_documents(self):
        raise NotImplementedError()

    def extract_text(self):
        raise NotImplementedError()

    def extract_metadata(self):
        return {}

    def make_id(self, source: str, source_doc: Dict):
        target_values = [source_doc[k] for k in self.TARGET_ID_KEYS]
        payload = f"{':'.join(target_values)}".encode()
        source_doc["id"] = f"{source}_{hashlib.sha256(payload).hexdigest()}"
        return

    def clean_text(self, text):
        return text

    def validate(self):
        raise NotImplementedError()