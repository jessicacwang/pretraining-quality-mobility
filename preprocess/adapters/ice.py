"""CorpusAdapter for ICE"""

from preprocess.adapters.base import BaseAdapter
from typing import Iterator, Tuple, Dict, List
from pathlib import Path
from collections import Counter
import re


class ICEAdapter(BaseAdapter):
    TARGET_ID_KEYS = ["component", "source_filename"]
    _ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    _CRLF = re.compile(r"\r")

    def __init__(self, root_path, file_pattern, tag_registry: Dict):
        super().__init__(root_path, file_pattern)
        self.name = "ice"
        self.nested_tags = 0
        self.tag_counts = Counter()
        self.current_doc = None
        self.empty_doc_ids = []

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

    def _generate_tag_pattern(self, tag_arr: List) -> List:
        return "|".join(sorted(tag_arr, key=len, reverse=True))

    def _iter_source_documents(self) -> Iterator[Path]:
        for path in self.path.glob(self.file_pattern):
            yield path

    def _count_localizations(self, source_text: str) -> Tuple[int]:
        foreign_counts = Counter(self._TREAT_AS_FOREIGN.findall(source_text))
        indig_counts = Counter(self._TREAT_AS_INDIG.findall(source_text))

        self.tag_counts += foreign_counts
        self.tag_counts += indig_counts

        n_foreign = sum(foreign_counts.values())
        n_indig = sum(indig_counts.values())
        return n_foreign, n_indig

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

    def extract_text(self, path: Path):
        for encoding in self._ENCODINGS:
            try:
                result = open(path, mode="r", encoding=encoding).read()
                return result
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(f"No encodings could decode the file: {str(path)}")

    def clean_text(self, text):
        result = self._CRLF.sub("", text)
        result = self._DROP_TAGS_ONLY.sub("", result)
        result = self._DROP_FULL_SPAN.sub("", result)
        for _, d in self._ALTERATION_MAP.items():
            result = d["pat"].sub(d["sub"], result)

        if not bool(result):
            self.empty_doc_ids.append(self.current_doc)
            self.empty_text_count += 1
        return result

    def validate(self):
        return {
            "ids_unique": len(self.ids_observed) == len(set(self.ids_observed)),
            "empty_text_count": self.empty_text_count,
            "empty_doc_ids": self.empty_doc_ids,
            "nested_spans": self.nested_tags,
            "tag_counts": self.tag_counts,
        }


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
        print(f"Failed at document {len(foo.ids_observed)}: {e}")
        raise  # re-raise so you get the full traceback
    finally:
        foo.cleanup()
    print(foo.validate())


if __name__ == "__main__":
    main()
