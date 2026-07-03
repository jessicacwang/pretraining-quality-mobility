import shutil
import re
from pathlib import Path
from typing import Dict, Any, List


class ComponentNormalizer:
    """Default class for reorganizing ICE components; does not handle ICE-EA."""

    _ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    _GENRE_ID_GROUPS_DEFAULT = {"genre": 1, "id": 2}
    _TARGET_TEMPLATE_DEFAULT = "{target_code}/ice_{target_code}_{genre}_{id}.txt"

    def __init__(
        self,
        name: str,
        dry_run: bool,
        source_base: Path,
        target_base: Path,
        config: Dict[str, Any],
    ):
        # Basics
        self.name = name
        self.dry_run = dry_run

        # Paths to keep track of
        self.source_root = source_base / Path(config["source_root"])
        self.target_code = config["target_code"]
        self.target_template = config.get(
            "target_template", self._TARGET_TEMPLATE_DEFAULT
        )
        self.target_base = target_base
        # File/line pattern to match and parameters
        self.extract_groups = config.get("extract", self._GENRE_ID_GROUPS_DEFAULT)
        self.case_insensitive = config.get("case_insensitive", False)
        self.flags = re.IGNORECASE if self.case_insensitive else 0
        self.pattern = re.compile(config.get("pattern"), flags=self.flags)

        # Genre code determiners
        self.normalize_genre = config.get("normalize_genre", False)

        # Results
        self.changes = []
        self.errors = []
        self.warnings = []
        self.unmatched = []

    # ======================== PATTERN MATCHING ==========================

    def _extract_metadata(self, rel_path: Path):
        match = self.pattern.match(str(rel_path))

        if not match:
            self.warnings.append(
                f"Filename didn't match pattern: {rel_path} (pattern: {self.pattern.pattern})"
            )
            return None

        metadata = dict()

        for field, group_num in self.extract_groups.items():
            metadata[field] = match.group(group_num)

        if self.normalize_genre:
            metadata["genre"] = metadata["genre"].upper()

        return metadata

    def _find_files(self) -> List[Path]:
        all_files = []

        for ext in ["*.txt", "*.TXT"]:
            all_files.extend(self.source_root.glob(f"**/{ext}"))

        matching = []
        for file_path in all_files:
            rel_path = file_path.relative_to(self.source_root)
            try:
                if self.pattern.match(str(rel_path)):
                    matching.append(file_path)
            except re.error as e:
                self.warnings.append(
                    f"Regex error with pattern '{self.pattern.pattern}' on file {rel_path}: {e}"
                )
                continue
        return matching

    # ======================== PROPOSE TARGET PATH ==========================

    def _propose_change(self, metadata: Dict[str, str]) -> Path:
        target_name = self.target_template

        for key, value in metadata.items():
            placeholder = f"{{{key}}}"
            target_name = target_name.replace(placeholder, value)

        target_name = target_name.replace("{target_code}", self.target_code)

        return self.target_base / Path(target_name)

    def _copy_file(self, source_path: Path, target_path: Path) -> None:
        if self.dry_run:
            return

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Edge case: target path already exists
        if target_path.exists():
            counter = 1
            stem = target_path.stem
            suffix = target_path.suffix

            # Update the target path with counter, stem and suffix values
            while target_path.exists():
                target_path = target_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            self.warnings.append(f"Duplicate resolved: {target_path.name}")

        shutil.copy2(source_path, target_path)
        self.changes.append({"from": source_path, "to": target_path})
        return

    # ======================== COMPONENT PROCESSING ==========================

    def _process_file(self, file_path: Path) -> Path:
        """Generate target path from original file path"""
        # Extract metadata
        rel_path = file_path.relative_to(self.source_root)
        metadata = self._extract_metadata(rel_path)

        if metadata is None:
            return

        # Store proposed change
        target_path = self._propose_change(metadata)

        # Execute and record actual change
        if not self.dry_run:
            self._copy_file(file_path, target_path)
        return

    def _validate_config(self) -> bool:
        if not self.source_root.exists():
            self.errors.append(
                f"{self.name} - Source root not found: {self.source_root}"
            )
            return False
        return True

    # ============= UNMATCHED FILE CHECK - VALIDATION =============
    def _check_unmatched_files(self) -> None:
        processed = {Path(c["from"]) for c in self.changes}

        all_files = set()
        if self.source_root.exists():
            for file_path in self.source_root.rglob("*.{txt,TXT}"):
                if file_path.is_file():
                    all_files.add(file_path)

        unmatched_files = all_files - processed

        if unmatched_files:
            print(f"\n [!!] Found {len(unmatched_files)} unmatched files:")
            for f in list(unmatched_files)[:10]:
                print(f"    - {f.relative_to(self.source_base)}")
            if len(unmatched_files) > 10:
                print(f"    ... and {len(unmatched_files) - 10} more")
            self.unmatched.extend(unmatched_files)
        return

    def run(self) -> Dict[str, List]:
        if not self._validate_config():
            return

        files = self._find_files()

        if not files:
            print(f"    [!!] No matching files found")
            return
        print(f"    Found {len(files)} files")

        for file_path in files:
            self._process_file(file_path)

        # Summary of changes
        print(f"    Proposed changes: {len(self.changes)}")
        print(f"    Errors: {len(self.errors)}")
        if self.errors:
            for error in self.errors[:5]:
                print(f"        => {error}")
        print(f"    Warnings: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings[:15]:
                print(f"        [!!] {warning}")

        self._check_unmatched_files()
        return self.changes, self.errors, self.warnings, self.unmatched


class AggregatedComponentNormalizer(ComponentNormalizer):
    """Base class for components with documents aggregated by category (genre or modality)"""

    def __init__(
        self,
        name: str,
        dry_run: bool,
        source_base: Path,
        target_base: Path,
        config: Dict[str, Any],
    ):
        super().__init__(name, dry_run, source_base, target_base, config)
        self.file__ENCODINGS = set()
        self.first_line_pattern = re.compile(
            config.get("first_line_pattern"), self.flags
        )
        self.metadata_pattern = None  # To be set by subclasses
        return

    def _copy_file(self, source_path: Path, target_path: Path, contents: str) -> None:
        if self.dry_run:
            return

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Edge case: target path already exists
        if target_path.exists():
            counter = 1
            stem = target_path.stem
            suffix = target_path.suffix

            # Update the target path with counter, stem and suffix values
            while target_path.exists():
                target_path = target_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            self.warnings.append(f"Duplicate resolved: {target_path.name}")

        # Write to a new file
        with open(target_path, "w", encoding=list(self.file__ENCODINGS).pop()) as f:
            f.write(contents)

        # Record change
        self.changes.append({"from": source_path, "to": target_path})
        return

    def _extract_metadata(self, doc_name: str):
        match = self.metadata_pattern.match(doc_name)

        if not match:
            self.warnings.append(
                f"Document name didn't match pattern: {doc_name} (pattern: {self.metadata_pattern.pattern})"
            )
            return None

        metadata = dict()

        for field, group_num in self.extract_groups.items():
            metadata[field] = match.group(group_num)

        if self.normalize_genre:
            metadata["genre"] = metadata["genre"].upper()
        return metadata

    def _parse_contents(self, contents: List[str]) -> Dict[str, str]:
        documents = dict()
        current_doc = None

        # Loop over lines, collecting documents and contents
        for line in contents:
            stripped = line.rstrip("\n")
            match = self.first_line_pattern.match(stripped)
            if match:
                current_doc = stripped
                documents[current_doc] = ""
            elif current_doc is not None:
                documents[current_doc] += line

        return documents

    def _split_file(self, file_path: Path):
        """Split the contents of a file into individual documents and codes"""
        for encoding in ComponentNormalizer._ENCODINGS:
            try:
                with open(file_path, mode="r", encoding=encoding) as f:
                    contents = f.readlines()
                    self.file__ENCODINGS.add(encoding)
                    return contents
            except (UnicodeDecodeError, UnicodeError):
                continue
        return

    def _process_file(self, file_path: Path):
        """Generate a set of target paths from an original file path, containing multiple documents"""
        # Read file
        contents = self._split_file(file_path)

        # Split by title string
        documents = self._parse_contents(contents)

        # Loop over documents
        for d in documents:
            metadata = self._extract_metadata(d)
            if metadata is None:
                continue
            # Store proposed change
            target_path = self._propose_change(metadata)

            # Execute and record actual change
            if not self.dry_run:
                self._copy_file(file_path, target_path, documents[d])
        return


class EAComponentNormalizer(AggregatedComponentNormalizer):
    """Class for ICE-EA reorganization; handles splitting of aggregated documents"""

    def __init__(
        self,
        name: str,
        dry_run: bool,
        source_base: Path,
        target_base: Path,
        config: Dict[str, Any],
    ):
        super().__init__(name, dry_run, source_base, target_base, config)
        self.country_mapping = config.get("country_mapping")
        self.metadata_pattern = self.first_line_pattern
        return

    def _propose_change(self, metadata: Dict[str, str]) -> None:
        target_name = self.target_template

        for key, value in metadata.items():
            placeholder = f"{{{key}}}"
            if key == "country":
                target_name = target_name.replace(
                    placeholder, self.country_mapping[value]
                )
            else:
                target_name = target_name.replace(placeholder, value)

        target_name = target_name.replace("{target_code}", self.target_code)

        return self.target_base / Path(target_name)


class GBComponentNormalizer(AggregatedComponentNormalizer):
    """Class for ICE-GB reorganization; handles splitting of exported aggregate documents"""

    def __init__(
        self,
        name: str,
        dry_run: bool,
        source_base: Path,
        target_base: Path,
        config: Dict[str, Any],
    ):
        super().__init__(name, dry_run, source_base, target_base, config)
        self.metadata_pattern = re.compile(config.get("metadata_pattern"), self.flags)
        return

    def _propose_change(self, metadata):
        return ComponentNormalizer._propose_change(self, metadata)

    def _parse_contents(self, contents: List[str]) -> Dict[str, str]:
        documents = dict()
        current_doc = None

        for line in contents:
            stripped = line.strip("\n")
            match = self.first_line_pattern.match(stripped)
            if match:
                current_doc = match.group(1)
                if current_doc not in documents:
                    documents[current_doc] = stripped
            elif current_doc is not None:
                documents[current_doc] += stripped
        return documents


class NGComponentNormalizer(ComponentNormalizer):
    """Class for ICE-NG reorganization; handles mapping of genre descriptions to codes."""

    def __init__(
        self,
        name: str,
        dry_run: bool,
        source_base: Path,
        target_base: Path,
        config: Dict[str, Any],
    ):
        super().__init__(name, dry_run, source_base, target_base, config)
        self.genre_map = config.get("genre_mapping", None)
        self.map_genre = config.get("map_genre", False)
        return

    # ================= GENRE MAPPING ====================
    def _map_genre(self, modality: str, genre: str) -> str:
        return self.genre_map[modality].get(genre, genre)

    def _extract_metadata(self, rel_path: Path):
        match = self.pattern.match(str(rel_path))

        if not match:
            self.warnings.append(
                f"Filename didn't match pattern: {rel_path} (pattern: {self.pattern.pattern})"
            )
            return None

        metadata = dict()

        for field, group_num in self.extract_groups.items():
            metadata[field] = match.group(group_num)

        # for ICE-NG specifically, map genre description to a code
        metadata["genre"] = self._map_genre(metadata["modality"], metadata["genre"])

        return metadata


if __name__ == "__main__":
    import json

    with open("preprocess/config/ice_dir_normalize.json", "r") as f:
        mapping = json.load(f)
    foo = GBComponentNormalizer(
        "ICE-GB",
        False,
        Path(mapping.get("source_base")),
        Path(mapping.get("target_base")),
        mapping.get("component_configs").get("ICE-GB"),
    )

    foo.run()
