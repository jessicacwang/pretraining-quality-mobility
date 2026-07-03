import argparse
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict


def parse_regex_targets(regex_file_path: str) -> Dict[int, Any]:
    result = dict()
    with open(regex_file_path, "r", encoding="utf-8") as regex_r:
        lines = regex_r.readlines()
        for idx, line in enumerate(lines, start=1):
            pattern = line.strip()
            try:
                result[idx] = re.compile(pattern)
            except re.error as e:
                print(idx)
                print(e)
                raise
    return result

def parse_inventory(tag_file_path: str) -> List[Tuple]:
    result = []
    _LINE_RE = re.compile(r"^\s*(\d+) (.+)$")
    with open(tag_file_path, mode="r", encoding="utf-8") as reader:
        lines = reader.readlines()
        for idx, line in enumerate(lines):
            match = _LINE_RE.match(line)
            if match:
                result.append(
                    (match.group(2), int(match.group(1)))
                )
            else:
                print(f"!! LINE {idx}: No match")
    return result

def track_hits(inventory: List[Tuple], regex_targets: Dict[int, Any]):
    report = defaultdict(
        lambda: {"total_count": 0, "distinct": 0}
    )
    # Loop over regex targets
    for line_num, regex in regex_targets.items():
        for tag, count in inventory:
            if regex.match(tag.lower()):
                report[line_num]["distinct"] += 1
                report[line_num]["total_count"] += count
    return report

def main(regex_file_path: str, tag_file_path: str):
    # Parse regex file
    regex_targets = parse_regex_targets(regex_file_path)

    # Parse inventory file
    inventory = parse_inventory(tag_file_path)

    # Track regex hits against inventory
    hits = track_hits(inventory, regex_targets)

    # Report
    print(f"{'regex':30} {'distinct hits':>9} {'total hits':>12}")
    running = 0
    total_occurrences = sum([count for _, count in inventory])
    for line_num, report in hits.items():
        print(f"{regex_targets[line_num].pattern:30} {report["distinct"]:>9} {report["total_count"]:>12}")
        running += report["total_count"]
    
    print(f"COVERAGE: {running / total_occurrences * 100:2f}% OF ALL OCCURRENCES")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--regex", required=True)
    parser.add_argument("--tags", required=True)
    args = parser.parse_args()
    main(args.regex, args.tags)