"""CorpusAdapter for ICE"""

from preprocess.adapters.base import BaseAdapter
from typing import Iterator, Tuple, Dict, List, Any
from pathlib import Path
from collections import Counter, defaultdict
import re


class ICEAdapter(BaseAdapter):
    TARGET_ID_KEYS = ("component", "source_filename")

    def __init__(self, root_path, file_pattern, tag_registry: Dict):
        super().__init__(root_path, file_pattern)
        self.name = "ice"
        self.full_name = "International Corpus of English"
        self.add_stat("foreign")
        self.add_stat("indigenous")
        self.add_stat("substitutions", defaultdict(int))
        self.add_stat("residual_tags")

        # Annotation tag attributes
        # Metadata tracking
        foreign_tags = self._generate_tag_pattern(tag_registry["treat_as_foreign"])
        self._TREAT_AS_FOREIGN = re.compile(f"(?:{foreign_tags})", flags=re.I)

        indig_tags = self._generate_tag_pattern(tag_registry["treat_as_indig"])
        self._TREAT_AS_INDIG = re.compile(f"(?:{indig_tags})", flags=re.I)

        # Cleaning actions
        self._ALTERATION_MAP = dict()
        for k, d in tag_registry["alter"].items():
            self._ALTERATION_MAP[k] = {
                "pat": re.compile(d["pat"], flags=re.IGNORECASE),
                "sub": d["sub"],
            }

        full_span_tags = self._generate_tag_pattern(tag_registry["drop_full_span"])
        self._DROP_FULL_SPAN = re.compile(
            f"<(?:{full_span_tags})>(?:(?!<(?:{full_span_tags})>).)*?</(?:{full_span_tags})>",
            flags=re.IGNORECASE | re.DOTALL,
        )

        tag_only_tags = self._generate_tag_pattern(tag_registry["drop_tag_only"])
        self._DROP_TAGS_ONLY = re.compile(f"(?:{tag_only_tags})", flags=re.I)

        self._temp_leu_tags = 0
        self._temp_cleaning_stats = {}
        self._temp_residual = 0
    # ==========================================================================
    # Subclass interface
    # ==========================================================================

    def _iter_source_documents(self) -> Iterator[Path]:
        for path in self.path.glob(self.file_pattern):
            yield path

    def _generate_tag_pattern(self, tag_arr: List) -> List:
        return "|".join(sorted(tag_arr, key=len, reverse=True))

    def _count_localizations(self, source_text: str) -> Tuple[int]:
        foreign_counts = Counter(self._TREAT_AS_FOREIGN.findall(source_text))
        indig_counts = Counter(self._TREAT_AS_INDIG.findall(source_text))

        n_foreign = sum(foreign_counts.values())
        n_indig = sum(indig_counts.values())

        return n_foreign, n_indig

    def extract_text(self, path: Path):
        for encoding in self._ENCODINGS:
            try:
                result = open(path, mode="r", encoding=encoding).read()
                if result.startswith("\ufeff"):
                    result = result[1:]
                return result
            except UnicodeDecodeError:
                continue

        raise ValueError(f"No encodings could decode the file: {str(path)}")

    def extract_metadata(self, file_path: Path, source_text: str):
        self.current_doc = str(file_path)
        # Inferred from file name metadata
        rel_path = file_path.relative_to(self.path)
        path_parts = str(rel_path).split("/")
        component = path_parts[0]
        genre = path_parts[1].split("_")[2]
        modality = "written" if genre[0] == "W" else "spoken"

        # Document internal metadata
        foreign_tags, indig_tags = self._count_localizations(source_text)

        return {
            "component": component,
            "source_filename": str(rel_path),
            "modality": modality,
            "genre": genre,
            "original": source_text,
            "foreign": foreign_tags,
            "indigenous": indig_tags,
        }

    def clean_text(self, text):
        result, crlf_n = self._CRLF.subn("", text)
        self._temp_cleaning_stats["crlf_removed"] = crlf_n
        
        result, drop_tag_n = self._DROP_TAGS_ONLY.subn("", result)
        self._temp_cleaning_stats["tags_dropped"] = drop_tag_n

        result, drop_span_n = self._DROP_FULL_SPAN.subn("", result)
        self._temp_cleaning_stats["spans_dropped"] = drop_span_n

        for alt, d in self._ALTERATION_MAP.items():
            result, pat_n = d["pat"].subn(d["sub"], result)
            self._temp_cleaning_stats[f"alter_{alt}"] = pat_n

        return result if len(result) else None

    def validate(self, text, metadata):
        residual = self._ANGLE_BRACKET_RE.findall(text)
        self._temp_residual = len(residual)

        return True, None
    
    # ==========================================================================
    # Corpus stats
    # ==========================================================================
    def update_stats(self, metadata):
        component = metadata["component"]
        # TODO: update documents written at component level
        comp_stats = self._stats["components"].setdefault(
            component,
            {
                "documents_written": 0,
                "extras": {
                    "foreign": 0,
                    "indigenous": 0,
                    "substitutions": defaultdict(int),
                    "residual_tags": 0
                }
            }
        )

        # Track LEU tags and reset the temp storage
        self._stats["extras"]["foreign"] += metadata["foreign"]
        self._stats["extras"]["indigenous"] += metadata["indigenous"]
        comp_stats["extras"]["foreign"] += metadata["foreign"]
        comp_stats["extras"]["indigenous"] += metadata["indigenous"]

        # Track tag cleaning and reset temp storage
        for key, count in self._temp_cleaning_stats.items():
            self._stats["extras"]["substitutions"][key] += count
            comp_stats["extras"]["substitutions"][key] += count

        self._temp_cleaning_stats = {}

        # Track residual tags and reset temp storage
        self._stats["extras"]["residual_tags"] += self._temp_residual
        comp_stats["extras"]["residual_tags"] += self._temp_residual
        self._temp_residual = 0

        # Update component level documents written
        comp_stats["documents_written"] += 1
        return

def main():
    import json

    registry = None
    with open("preprocess/config/unify.json", "r") as f:
        temp = json.load(f)
        registry = temp["corpora"]["ice"]["tag_registry"]

    foo = ICEAdapter("../data/ice", "**/*.txt", registry)

    foo.prepare()
    try:
        docs = list(foo.iter_documents())
        print(f"Successfully processed {len(docs)} documents")
        if docs:
            print(f"Sample doc: {docs[0]}")
    except Exception as e:
        print(f"Failed at document {foo.get_stats()["documents_seen"]}: {e}")
        raise  # re-raise so you get the full traceback
    finally:
        foo.cleanup()
    stats = foo.get_stats()
    print(f"\nStats:")
    print(f"  Seen: {stats['documents_seen']}")
    print(f"  Written: {stats['documents_written']}")
    print(f"  Dropped: {stats['documents_dropped']}")
    print(f"  LEU tags: {len(stats['extras'].get('leu_tags', {}))}")
    print(f"  Substitutions: {stats['extras'].get('substitutions', {})}")
    print(f"  Residual tags: {stats['extras'].get('residual_tags', 0)}")


if __name__ == "__main__":
    main()
