"""CorpusAdapter for GloWbe"""

from preprocess.adapters.base import BaseAdapter
from typing import Iterator
from pathlib import Path
import zipfile
import re
import trafilatura
import tempfile
from typing import Dict
from nltk.tokenize import PunktSentenceTokenizer


class GloWbeAdapter(BaseAdapter):
    TARGET_ID_KEYS = ["component", "source_filename", "glowbe_doc_id"]
    _ANGLE_BRACKET_RE = re.compile("<.*?>", flags=re.DOTALL)
    _CRLF = re.compile(r"\r")

    def __init__(self, root_path, file_pattern):
        super().__init__(root_path, file_pattern)
        self.name = "glowbe"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.extract_dir = Path(self.temp_dir.name)
        self.obfuscated_count = 0
        self.tokenizer = PunktSentenceTokenizer()
        self.current_doc = None
        self.empty_doc_ids = []

    # ====================== BEFORE ITERATING ========================
    def prepare(self):
        for path in self.path.glob(self.file_pattern):
            # unzip .zip
            with zipfile.ZipFile(path, "r") as archive:
                archive.extractall(self.extract_dir)

    def cleanup(self):
        if self.temp_dir is not None:
            self.temp_dir.cleanup()

    # ====================== HELPERS ========================
    def _parse_line(self, line: str) -> tuple[str, str]:
        try:
            glowbe_doc_id, glowbe_text = line[2:].split(" ", maxsplit=1)
        except ValueError:
            raise ValueError("Could not split line into GloWbe doc_id and text")

        if not glowbe_doc_id:
            raise ValueError("Missing GloWbe document ID")

        if not glowbe_text:
            raise ValueError("Missing GloWbe document text")

        return glowbe_doc_id, glowbe_text

    def _iter_source_documents(self) -> Iterator[Path]:
        for txt_file in self.extract_dir.glob("*.txt"):
            file_name = txt_file.name
            file_genre = (
                "blog" if file_name.split("_")[-1].startswith("b") else "general"
            )
            file_component = file_name.split("_")[1]
            with open(txt_file, "r", encoding="ascii", newline="") as f:
                for line in f:
                    line = line.rstrip("\r\n")

                    if not line.startswith("##"):  # First line case
                        continue

                    glowbe_doc_id, glowbe_text = self._parse_line(line)

                    yield {
                        "component": file_component,
                        "source_filename": file_name,
                        "glowbe_doc_id": glowbe_doc_id,
                        "glowbe_text": glowbe_text,
                        "genre": file_genre,
                    }

    def extract_metadata(self, source_doc: Dict, source_text: str):
        # attrs: source_filename, glowbe_doc_id, genre (general or blog)
        self.current_doc = source_doc["glowbe_doc_id"]
        return {
            "component": source_doc["component"],
            "source_filename": source_doc["source_filename"],
            "glowbe_doc_id": source_doc["glowbe_doc_id"],
            "genre": source_doc["genre"],
            "original": source_text,
            "obfuscated": source_text.count("@ @ @ @ @ @ @ @ @ @"),
        }

    def extract_text(self, source_doc):
        # return text after ##<doc_id>
        result = source_doc["glowbe_text"]
        return result

    def clean_text(self, text):
        clean = ""
        # remove garbled content surrounding '@' symbols
        for start, end in self.tokenizer.span_tokenize(text):
            if "@ @ @ @ @ @ @ @ @ @" in text[start:end]:
                self.obfuscated_count += 1
                continue
            else:
                clean += text[start:end]
        result = self._CRLF.sub("", clean)
        # result = self._ANGLE_BRACKET_RE.sub("", result)
        result = trafilatura.extract(clean, favor_recall=True)
        if not bool(result):
            self.empty_doc_ids.append(self.current_doc)
            self.empty_text_count += 1
        return result

    # ====================== FINAL VALIDATION ========================
    def validate(self):
        return {
            "ids_unique": len(self.ids_observed) == len(set(self.ids_observed)),
            "empty_text_count": self.empty_text_count,
            "empty_doc_ids": self.empty_doc_ids,
            "obfuscated_count": self.obfuscated_count,
        }


def main():
    foo = GloWbeAdapter("../toy-data/glowbe/glowbe-text", "*.zip")

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
