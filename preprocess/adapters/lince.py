"""CorpusAdapter for LinCE"""
import csv
from ast import literal_eval
from typing import Iterator, Dict, List
from data import UnifiedText
from preprocess.adapters.base import BaseAdapter
from collections import Counter

class LinCEAdapter(BaseAdapter):
    OTHER_LABELS = ["other", "eng&spa", "rest", "mixed"]
    SOURCE_KEYS = ["idx", "words", "lid", "component", "non_english", "split"]
    TARGET_ID_KEYS = ["component", "non_english", "split", "idx"]

    def __init__(self, root_path, file_pattern):
        super().__init__(root_path, file_pattern)
        self.name = "lince"
        self.labels_observed = set()
        self.ids_observed = list()
        self.docs_dropped = 0
        
    def _iter_source_documents(self) -> Iterator[Dict]:
        # loop over eng train and validation docs
        for file_path in self.path.glob(self.file_pattern):
        #     # parse filename into source, task, non_english, split fields
            file_parts = str(file_path).split("_")
            component = file_parts[0].split("/")[-1]
            non_english = file_parts[1].replace("eng", "")
            split = file_parts[2].replace(".csv", "")

            file_info = {
                "component": component,
                "non_english": non_english,
                "split": split
            }
            with open(file_path, "r", encoding="utf-8") as f:
                file_reader = csv.DictReader(f)
                # loop over rows
                for row in file_reader:
                    row["words"] = row["words"].replace(" ", ", ")
                    row["lid"] = row["lid"].replace(" ", ", ")
                    row["words"] = literal_eval(row["words"])
                    row["lid"] = literal_eval(row["lid"])

                    # Skip rows if they don't have LID labels
                    if ''.join(row["lid"]) == "":
                        self.docs_dropped += 1
                        continue
                    else:
                        # Update global labels observed
                        self.labels_observed |= set(row["lid"])

                        # add file-level properties to row
                        row |= file_info

                        # yield result
                        yield {key: row[key] for key in self.SOURCE_KEYS if key in row}
    
    def _compute_cmi(self, lid: List[str]) -> int:
        lid_counts = Counter(lid)

        # n = total tokens
        n = sum(lid_counts.values())

        # u = tokens with non-language labels
        u = sum([v for k, v in lid_counts.items() if k in self.OTHER_LABELS])
        
        # Base case from Das & Gambäck 2014
        if n == u:
            return 0
        elif n < u: # Safeguard
            return None
        else:
            # most common label used = max(w_i)
            max_w_i = [c for c in lid_counts.most_common() if c[0] not in self.OTHER_LABELS][0][1]
            return 1 - (max_w_i/(n - u))
    
    def extract_text(self, source_doc):
        """Create whitespace joined text"""
        # Create new field
        result = ' '.join(source_doc["words"])

        # Increment if empty
        self.empty_text_count += len(result) == 0
        return result
    
    def extract_metadata(self, source_doc):
        """Compute CMI"""
        # Compute score
        score = self._compute_cmi(source_doc["lid"])
        
        return {
            "cmi": score,
            "component": source_doc["component"],
            "non_english": source_doc["non_english"],
            "split": source_doc["split"],
            "idx": source_doc["idx"]
        }

    def make_id(self, source_doc):
        # Make ID
        super().make_id(source_doc)
        return
    
    def validate(self):
        return {
            "ids_unique": len(self.ids_observed) == len(set(self.ids_observed)),
            "empty_text_count": self.empty_text_count,
            "docs_dropped": self.docs_dropped,
            "labels_observed": list(self.labels_observed)
        }
    
    def clean_text(self, text):
        return super().clean_text(text)
    
    # ====================== ENTRY POINT ======================
    
    def iter_documents(self):
        for source_doc in self._iter_source_documents():
            # join words to new text field
            text = self.extract_text(source_doc)
            text = self.clean_text(text)
            metadata = self.extract_metadata(source_doc)
    
            yield UnifiedText(
                id=self.make_id(metadata),
                text=text,
                metadata=metadata
            )
    
def main():
    foo = LinCEAdapter("../data/lince-kaggle", "*_*eng_*.csv")
    
    try:
        docs = list(foo.iter_documents())
        print(f"Successfully processed {len(docs)} documents")
        if docs:
            print(f"Sample doc: {docs[0]}")
    except Exception as e:
        print(f"Failed at document {len(foo.ids_observed)}: {e}")
        raise  # re-raise so you get the full traceback
    
    print(foo.validate())

if __name__ == "__main__":
    main()