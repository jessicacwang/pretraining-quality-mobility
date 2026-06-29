"""Base class for CorpusAdapter objects: disover documents, construct IDs, extract metadata and prepare text"""
from pathlib import Path
from typing import Dict
from data import UnifiedText

class BaseAdapter:
    TARGET_ID_KEYS = []    
    def __init__(self, root_path: str, file_pattern: str):
        self.name = ""
        self.path = Path(root_path)
        self.file_pattern = file_pattern
        self.ids_observed = list()
        self.empty_text_count = 0
        return
    
    def _iter_source_documents(self):
        raise NotImplementedError()

    def extract_text(self):
        raise NotImplementedError()

    def extract_metadata(self):
        return {}

    def make_id(self, metadata: Dict):
        target_values = [metadata[k] for k in self.TARGET_ID_KEYS]
        payload = f"{':'.join(target_values)}"
        result = f"{self.name}_{payload}"
        # Add ID to the list seen
        self.ids_observed.append(result)
        return result

    def clean_text(self, text):
        return text

    def validate(self):
        raise NotImplementedError()
    
    def prepare(self):
        pass

    def cleanup(self):
        pass

    # ====================== ENTRY POINT ======================
    def iter_documents(self):
        for source_doc in self._iter_source_documents():
            # join words to new text field
            text = self.extract_text(source_doc)
            metadata = self.extract_metadata(source_doc)
            text = self.clean_text(text)
    
            yield UnifiedText(
                id=self.make_id(metadata),
                text=text,
                metadata=metadata
            )