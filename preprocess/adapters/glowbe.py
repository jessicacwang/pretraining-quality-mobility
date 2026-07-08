"""CorpusAdapter for GloWbe"""

from preprocess.adapters.base import BaseAdapter
from typing import Iterator
from pathlib import Path
import zipfile
import tempfile
from typing import Dict
from nltk.tokenize import PunktSentenceTokenizer


class GloWbeAdapter(BaseAdapter):
    TARGET_ID_KEYS = ("component", "source_filename", "glowbe_line_num", "glowbe_doc_id")

    def __init__(self, root_path, file_pattern):
        super().__init__(root_path, file_pattern)
        self.name = "glowbe"
        self.full_name = "Global Corpus of Web-based English"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.extract_dir = Path(self.temp_dir.name)
        self.tokenizer = PunktSentenceTokenizer()
        self.add_stat("obfuscated_spans")

    # ==========================================================================
    # Resource lifecycle
    # ==========================================================================
    def prepare(self):
        for path in self.path.glob(self.file_pattern):
            # unzip .zip
            with zipfile.ZipFile(path, "r") as archive:
                archive.extractall(self.extract_dir)

    def cleanup(self):
        if self.temp_dir is not None:
            self.temp_dir.cleanup()

    # ==========================================================================
    # Subclass interface
    # ==========================================================================
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

    def _parse_file(self, txt_file: str) -> Iterator[str, str]:
        for encoding in self._ENCODINGS:
            try:
                with open(txt_file, "r", encoding=encoding, errors="replace", newline="") as f:
                    for line in f:
                        line = line.rstrip("\r\n")

                        if not line.startswith("##"):  # First line case
                            continue

                        try:
                            glowbe_doc_id, glowbe_text = self._parse_line(line)
                            yield glowbe_doc_id, glowbe_text
                        except ValueError as e:
                            print(f"Warning: skipping malformed line in {txt_file}: {e}")
                            continue
                return
            except UnicodeDecodeError:
                continue

        raise ValueError(f"No encoding could decode the file {txt_file}")

    def _iter_source_documents(self) -> Iterator[Path]:
        for txt_file in self.extract_dir.glob("*.txt"):
            file_name = txt_file.name
            file_genre = (
                "blog" if file_name.split("_")[-1].startswith("b") else "general"
            )
            file_component = file_name.split("_")[1]
            
            for line_num, (glowbe_doc_id, glowbe_text) in enumerate(self._parse_file(txt_file), start=1):
                yield {
                    "component": file_component,
                    "source_filename": file_name,
                    "glowbe_doc_id": glowbe_doc_id,
                    "glowbe_line_num": str(line_num),
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
            "glowbe_line_num": source_doc["glowbe_line_num"],
            "genre": source_doc["genre"],
            "obfuscated_spans": source_text.count("@ @ @ @ @ @ @ @ @ @"),
        }

    def extract_text(self, source_doc):
        # return text after ##<doc_id>
        result = source_doc["glowbe_text"]
        return result if len(result) else None
    
    def clean_text(self, text):
        clean = ""
        # remove garbled content surrounding '@' symbols
        for start, end in self.tokenizer.span_tokenize(text):
            if "@ @ @ @ @ @ @ @ @ @" in text[start:end]:
                continue
            else:
                clean += text[start:end]
        result = self._CRLF.sub("", clean)
        result = self._ANGLE_BRACKET_RE.sub("", result)
        return result

    def validate(self, text, metadata):
        if len(text) == len(metadata["original"]):
            return False, "cleaning_no_effect"
        return True, None

    # ==========================================================================
    # Corpus stats
    # ==========================================================================
    def update_stats(self, metadata):
        component = metadata["component"]

        comp_stats = self._stats["components"].setdefault(
            component,
            {
                "documents_written": 0,
                "extras": {
                    "obfuscated_spans": 0
                }
            }
        )

        self._stats["extras"]["obfuscated_spans"] += metadata["obfuscated_spans"]
        comp_stats["extras"]["obfuscated_spans"] += metadata["obfuscated_spans"]

        # Update component level documents written
        comp_stats["documents_written"] += 1
        return

def main():
    foo = GloWbeAdapter("../toy-data/glowbe/glowbe-text", "*.zip")

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
    print(foo.get_stats())


if __name__ == "__main__":
    main()
