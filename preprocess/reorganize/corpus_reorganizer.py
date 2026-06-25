import json
from pathlib import Path
from typing import Dict, Any
from preprocess.reorganize.component_reorganizer import *


class CorpusReorganizer:

    def __init__(self, mapping_file: str, dry_run: bool = True):
        """Generates proposed reorganization from components and executes changes."""
        self.dry_run = dry_run
        self.mapping = self._load_mapping(mapping_file)
        self.source_base = Path(self.mapping.get("source_base"))
        self.target_base = Path(self.mapping.get("target_base"))
        self.genre_map = self.mapping.get("genre_mapping")
        self.components = self.mapping.get("component_configs")
        # Track results
        self.changes = []
        self.errors = []
        self.warnings = []
        self.unmatched = []

        # ============= FILE OPERATIONS =============

    # Load mapping JSON
    def _load_mapping(self, mapping_file: str) -> Dict[str, Any]:
        with open(mapping_file, "r") as f:
            return json.load(f)

    # ============= COMPONENT PROCESSING =============
    def _process_component(self, component_name: str, config: Dict[str, Any]):
        if component_name == "ICE-EA":
            component_reorganizer = EAComponentReorganizer(
                component_name, self.dry_run, self.source_base, self.target_base, config
            )
        elif component_name == "ICE-NG":
            component_reorganizer = NGComponentReorganizer(
                component_name, self.dry_run, self.source_base, self.target_base, config
            )
        else:
            component_reorganizer = ComponentReorganizer(
                component_name, self.dry_run, self.source_base, self.target_base, config
            )

        return component_reorganizer.run()

    def run(self) -> None:
        # Print header
        print("=" * 70)
        print(f"Source directory: {self.source_base}")
        print(f"Target directory: {self.target_base}")
        print(f"MODE: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print("=" * 70)

        # Process each regional component
        for component_name, config in self.mapping["component_configs"].items():
            print(f"{component_name} --> {self.target_base}/{config["target_code"]}")
            changes, errors, warnings, unmatched = self._process_component(
                component_name, config
            )
            self.changes.extend(changes)
            self.errors.extend(errors)
            self.warnings.extend(warnings)
            self.unmatched.extend(unmatched)

        # Summary
        print("\n" + "=" * 70)
        print(f"    Total files processed: {len(self.changes)}")
        print(f"    Errors: {len(self.errors)}")
        if self.errors:
            for error in self.errors[:5]:
                print(f"        => {error}")
        print(f"    Warnings: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings[:15]:
                print(f"        [!!] {warning}")
        print(f"    Unmatched: {len(self.unmatched)}")
        return
