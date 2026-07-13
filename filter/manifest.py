"""Defines specific preprocess functions for the FilterManifest class"""

from manifest import BaseManifest
from typing import Dict, Any

class FilterManifest(BaseManifest):
    def __init__(self, path):
        super().__init__(path)