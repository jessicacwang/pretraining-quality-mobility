"""CorpusAdapter for LinCE"""

import csv
from ast import literal_eval
from typing import Iterator, Dict, List
from preprocess.adapters.base import BaseAdapter
from collections import Counter, defaultdict


class LinCEAdapter(BaseAdapter):
    OTHER_LABELS = ("other", "eng&spa", "rest", "mixed")
    SOURCE_KEYS = ("idx", "words", "lid")
    TARGET_ID_KEYS = ("component", "non_english", "source_filename", "idx")

    def __init__(self, root_path, file_pattern):
        super().__init__(root_path, file_pattern)
        self.name = "lince"
        self.full_name = "Linguistic Code-switching Evaluation Benchmark"
        self.add_stat("labels_observed", set())
        self.add_stat("cmi_sum")
        self.add_stat("cmi_count")
        self._temp_labels = [] # to track LID labels outside of stats/metadata

    # ==========================================================================
    # Subclass interface
    # ==========================================================================
    def _parse_row(self, row: Dict, file_info: Dict) -> Dict:
        row["words"] = row["words"].replace(" ", ", ")
        row["lid"] = row["lid"].replace(" ", ", ")
        row["words"] = literal_eval(row["words"])
        row["lid"] = literal_eval(row["lid"])

        # Skip rows if they don't have LID labels
        if "".join(row["lid"]) == "":
            return None
        else:
            # filter keys
            row = {key: row[key] for key in self.SOURCE_KEYS if key in row}

            # add file-level properties to row
            row |= file_info

        return row
    
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
                "split": split,
                "source_filename": file_path.stem,
            }
            with open(file_path, "r", encoding="utf-8") as f:
                file_reader = csv.DictReader(f)
                # loop over rows
                for row in file_reader:
                    doc = self._parse_row(row, file_info)

                    if doc:
                        yield doc

    def _compute_cmi(self, lid: List[str]) -> int:
        lid_counts = Counter(lid)

        # n = total tokens
        n = sum(lid_counts.values())

        # u = tokens with non-language labels
        u = sum([v for k, v in lid_counts.items() if k in self.OTHER_LABELS])

        # Base case from Das & Gambäck 2014
        if n == u:
            return 0.0
        elif n < u:  # Safeguard
            return None
        else:
            # find non-other labels
            non_other_counts = [
                c for c in lid_counts.most_common() if c[0] not in self.OTHER_LABELS
            ]
            if not non_other_counts:
                return 0.0
            
            # most common non-other label is max_w_i
            max_w_i = non_other_counts[0][1]

            return 1 - (max_w_i / (n - u))

    def extract_text(self, source_doc):
        """Create whitespace joined text"""
        # Create new field
        if "".join(source_doc["words"]) == "":
            return None
        return " ".join(source_doc["words"])

    def extract_metadata(self, source_doc: Dict, source_text: str = None):
        """Provenance metadata and CMI"""
        # Compute score
        score = self._compute_cmi(source_doc["lid"])

        # Store labels temporarily
        self._temp_labels = source_doc["lid"]

        return {
            "component": source_doc["component"],
            "source_filename": source_doc["source_filename"],
            "non_english": source_doc["non_english"],
            "split": source_doc["split"],
            "idx": source_doc["idx"],
            "cmi": score,
        }

    def validate(self, text, metadata):
        cmi = metadata["cmi"]

        if cmi is None:
            return False, "missing_cmi"
        
        # CMI should be between 0 and 1
        if not (0 <= cmi <= 1):
            return False, "invalid_cmi_score"
        
        return True, None
    # ==========================================================================
    # Corpus stats
    # ==========================================================================
    def update_stats(self, metadata):
        """Record CMI and labels observed and component documents written"""
        component = metadata["component"]
        labels = self._temp_labels
        cmi = metadata["cmi"]

        # Track labels at corpus level
        self._stats["extras"]["labels_observed"] |= set(labels)

        # Track labels at component level
        comp_stats = self._stats["components"].setdefault(
            component,
            {
                "documents_written": 0,
                "extras": {
                    "labels_observed": set(),
                    "cmi_sum": 0,
                    "cmi_count": 0
                }
            }
        )

        comp_stats["extras"]["labels_observed"] |= set(labels)

        # Track CMI: corpus level
        self._stats["extras"]["cmi_sum"] += cmi 
        self._stats["extras"]["cmi_count"] += 1

        # Track CMI: component level
        comp_stats["extras"]["cmi_sum"] += cmi 
        comp_stats["extras"]["cmi_count"] += 1

        # Clear temp labels
        self._temp_labels = []
        return
    
    def _compute_average_cmi(self, cmi_sum: int, cmi_count: int) -> int:
        """Compute average CMI score"""
        return cmi_sum / cmi_count
    
    def get_stats(self):
        """Override to compute averages from sums/counts"""
        stats = super().get_stats()

        if stats["extras"]["cmi_count"] > 0:
            stats["extras"]["average_cmi"] = self._compute_average_cmi(
                stats["extras"]["cmi_sum"], stats["extras"]["cmi_count"]
            )

        for comp_stats in stats["components"].values():
            if comp_stats["extras"]["cmi_count"] > 0:
                comp_stats["extras"]["average_cmi"] = self._compute_average_cmi(
                    comp_stats["extras"]["cmi_sum"],
                    comp_stats["extras"]["cmi_count"]
                )
        
        return stats

def main():
    foo = LinCEAdapter("../data/lince-kaggle", "*_*eng_*.csv")

    try:
        docs = list(foo.iter_documents())
        print(f"Successfully processed {len(docs)} documents")
        if docs:
            print(f"Sample doc: {docs[0]}")
    except Exception as e:
        print(f"Failed at document {foo.get_stats()["documents_seen"]}: {e}")
        raise  # re-raise so you get the full traceback

    stats = foo.get_stats()
    print(f"\nStats:")
    print(f"  Seen: {stats['documents_seen']}")
    print(f"  Written: {stats['documents_written']}")
    print(f"  Dropped: {stats['documents_dropped']}")
    print(f"  Avg CMI: {stats['extras'].get('average_cmi')}")
    print(f"  Labels observed: {len(stats['extras'].get('labels_observed', set()))}")
    print(f"  Components: {list(stats['components'].keys())}")


if __name__ == "__main__":
    main()
