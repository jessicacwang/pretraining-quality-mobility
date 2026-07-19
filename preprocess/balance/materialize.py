import gzip
import json

def write(config: dict, id_to_output_key: dict, writers: dict):
    # Load LEU data and use map to write records
    with gzip.open(config["leu_data"], "rt") as leu_data:
        for line_num, leu_line in enumerate(leu_data, 1):
            try:
                doc = json.loads(leu_line)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                continue

            doc_id = doc.get("id")

            if doc_id.startswith("lince"):
                continue

            output_key = id_to_output_key.get(doc_id)

            if output_key is None:
                continue

            writers[output_key].write(json.dumps(doc) + "\n")