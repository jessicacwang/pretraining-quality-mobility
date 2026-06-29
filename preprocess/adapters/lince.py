"""CorpusAdapter for LinCE"""
import csv
from ast import literal_eval
from typing import Iterator, Dict, List, Any
from preprocess.adapters.base import BaseAdapter
from collections import Counter

class LinCEAdapter(BaseAdapter):
    OTHER_LABELS = ["other", "eng&spa", "rest", "mixed"]
    SOURCE_KEYS = ["idx", "words", "lid", "component", "non_english", "split"]
    TARGET_ID_KEYS = ["component", "split", "idx"]

    def __init__(self, root_path, file_pattern):
        super().__init__(root_path, file_pattern)
        self.labels_observed = set()
        self.ids_observed = list()
        self.total_docs = 0
        self.docs_dropped = 0
        self.empty_doc_count = 0
        
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
                        # add file-level properties to row
                        row |= file_info
                        # yield row
                        yield {key: row[key] for key in self.SOURCE_KEYS if key in row}
        return
    
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
        """Create whitespace joined text and drop words field"""
        # Create new field
        source_doc["text"] = ' '.join(source_doc["words"])

        # Increment if empty
        self.empty_doc_count += len(source_doc["words"]) == 0

        # Drop field
        del source_doc["words"]
        return
    
    def extract_metadata(self, source_doc):
        """Compute CMI and drop lid field"""
        # Compute score
        source_doc["cmi"] = self._compute_cmi(source_doc["lid"])
        
        # Update global labels observed
        self.labels_observed |= set(source_doc["lid"])

        # Drop field
        del source_doc["lid"]
        return

    def make_id(self, source, source_doc):
        # Make ID
        super().make_id(source, source_doc)

        # Add ID to the list seen
        self.ids_observed.append(source_doc["id"])
        return
    
    def validate(self):
        return {
            "ids_unique": len(self.ids_observed) == len(set(self.ids_observed)),
            "total_docs": self.total_docs,
            "empty_doc_count": self.empty_doc_count,
            "docs_dropped": self.docs_dropped,
            "labels_observed": list(self.labels_observed)
        }
    
    # ====================== ENTRY POINT ======================
    
    def iter_documents(self):
        for source_doc in self._iter_source_documents():
            # Compute CMI on original LID labels
            self.extract_metadata(source_doc)

            # join words to new text field
            self.extract_text(source_doc)

            # make ID
            self.make_id("lince", source_doc)

            self.total_docs += 1
            yield source_doc
    
def main():
    foo = LinCEAdapter("data/lince-kaggle", "*_*eng_*.csv")
    list(foo.iter_documents())
    print(foo.validate())
    return

if __name__ == "__main__":
    main()