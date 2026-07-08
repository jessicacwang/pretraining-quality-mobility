"""Base class for CorpusAdapter objects: disover documents, construct IDs, extract metadata and prepare text"""

from pathlib import Path
from typing import Dict, Iterator
from data import UnifiedText
from copy import deepcopy
import re


class BaseAdapter:
    TARGET_ID_KEYS = tuple()
    _ENCODINGS = ("utf-8", "latin-1", "cp1252", "iso-8859-1", "utf-16", "utf-16le", "utf-16be")
    _CRLF = re.compile(r"\r")
    _ANGLE_BRACKET_RE = re.compile("<.*?>", flags=re.DOTALL)

    def __init__(self, root_path: str, file_pattern: str):
        self.name = ""
        self.path = Path(root_path)
        self.file_pattern = file_pattern
        self._stats = {
            "documents_seen": 0,
            "documents_written": 0,
            "documents_dropped": {},
            "duplicate_ids": 0,
            "components": {},  # placeholder for component-level stats
            "extras": {},  # placeholder for corpus-specific extra stats
        }
        self._ids_seen = set()
        return

    # ==========================================================================
    # Subclass interface
    # ==========================================================================

    def _iter_source_documents(self):
        raise NotImplementedError()

    def extract_text(self):
        raise NotImplementedError()

    def extract_metadata(self):
        return {}

    def clean_text(self, text):
        return text if len(text) else None

    def validate(self):
        raise NotImplementedError()

    # ==========================================================================
    # Resource lifecycle
    # ==========================================================================

    def prepare(self):
        pass

    def cleanup(self):
        pass

    # ==========================================================================
    # ID construction
    # ==========================================================================
    def make_id(self, metadata: Dict):
        target_values = [metadata[k] for k in self.TARGET_ID_KEYS]
        payload = f"{':'.join(target_values)}"
        result = f"{self.name}_{payload}"

        # Add ID to the list seen
        if result in self._ids_seen:
            self._stats["duplicate_ids"] += 1
            raise ValueError(f"Duplicate document ID: {result}")

        self._ids_seen.add(result)
        return result

    # ==========================================================================
    # Corpus stats
    # ==========================================================================
    def record_seen(self):
        self._stats["documents_seen"] += 1

    def record_written(self):
        self._stats["documents_written"] += 1

    def record_drop(self, reason: str):
        dropped = self._stats["documents_dropped"]
        dropped[reason] = dropped.get(reason, 0) + 1

    def get_stats(self) -> Dict:
        return deepcopy(self._stats)

    def add_stat(self, key, initial_value=0):
        self._stats["extras"][key] = initial_value

    def update_stats(self, metadata):
        pass

    # ==========================================================================
    # Main entry point
    # ==========================================================================
    def iter_documents(self) -> Iterator[UnifiedText]:
        for source_doc in self._iter_source_documents():

            self.record_seen()

            text = self.extract_text(source_doc)

            if not text:
                self.record_drop("no_text")
                continue

            metadata = self.extract_metadata(source_doc, text)

            text = self.clean_text(text)

            if not text:
                self.record_drop("empty_after_cleaning")
                continue

            valid, reason = self.validate(text, metadata)

            if not valid:
                self.record_drop(reason)
                continue

            doc_id = self.make_id(metadata)

            self.record_written()

            self.update_stats(metadata)

            yield UnifiedText(id=doc_id, text=text, metadata=metadata)
