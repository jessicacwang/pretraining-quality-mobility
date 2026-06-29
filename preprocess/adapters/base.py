"""Base class for CorpusAdapter objects: disover documents, construct IDs, extract metadata and prepare text"""
from pathlib import Path
import hashlib
from typing import Dict

class BaseAdapter:
    TARGET_ID_KEYS = []    
    def __init__(self, root_path: str, file_pattern: str):
        self.path = Path(root_path)
        self.file_pattern = file_pattern
        self.ids_observed = list()
        return
    
    def _iter_source_documents(self):
        raise NotImplementedError()

    def extract_text(self):
        raise NotImplementedError()

    def extract_metadata(self):
        return {}

    def make_id(self, source: str, metadata: Dict):
        target_values = [metadata[k] for k in self.TARGET_ID_KEYS]
        payload = f"{':'.join(target_values)}".encode()
        result = f"{source}_{hashlib.sha256(payload).hexdigest()}"
        # Add ID to the list seen
        self.ids_observed.append(result)
        return result

    def clean_text(self, text):
        return text

    def validate(self):
        raise NotImplementedError()