"""Defines specific preprocess functions for the PreprocessManifest class"""
from typing import Any
from manifest import BaseManifest

class PreprocessManifest(BaseManifest):
    def init_corpus(self, step: str, corpus: str) -> None:
        self.data["steps"][step].setdefault("corpora", {})
        self.data["steps"][step]["corpora"].setdefault(corpus, {
            "files_input": 0,
            "documents_written": 0,
            "documents_dropped": 0,
            "drop_reasons": {},
            "validation": {}
        })
    
    def increment_drop(self, step: str, corpus: str, reason: str, n: int = 1) -> None:
        c = self.data["steps"][step]["corpora"][corpus]
        c["drop_reasons"][reason]
        return
    
    def increment_validation(self, step: str, corpus: str, reason: str, n: int = 1):
        c = self.data["steps"][step]["corpora"][corpus]
        c["validation"][reason]
        return
    
    def increment(self, step: str, path: list[str], n: int = 1):
        # Start traversing the data from the current step
        node = self.data["steps"][step]

        # Traverse the pointer down the dictionary path
        for key in path[:-1]:
            node = node.setdefault(key, {})
        
        # Point to field to increment
        leaf = path[-1]
        node[leaf] = node.get(leaf, 0) + n
        return

    def set_field(self, step: str, path: list[str], value: Any):
        # Start traversing the data from the current step
        node = self.data["steps"][step]

        # Traverse the pointer down the dictionary path
        for key in path[:-1]:
            node = node.setdefault(key, {})
        
        # Point to field to increment
        leaf = path[-1]
        node[leaf] = value
        return
