import gzip
import json
from tqdm import tqdm


def write(leu_data_file: str, id_to_output_key: dict, writers: dict):
    # Load LEU data and use map to write records
    with gzip.open(leu_data_file, "rt") as leu_data:
        for line_num, leu_line in enumerate(tqdm(leu_data, desc="LEU data"), 1):
            try:
                doc = json.loads(leu_line)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                continue

            doc_id = doc.get("id")

            output_key = id_to_output_key.get(
                doc_id, None
            )  # default value catches LinCE handling

            if output_key is None:
                continue

            writers[output_key].write(json.dumps(doc) + "\n")
