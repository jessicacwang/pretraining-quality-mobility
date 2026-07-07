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
                result[idx] = re.compile(pattern, flags=re.IGNORECASE)
            except re.error as e:
                print(idx, line)
                print(e)
                raise
    return result


def parse_inventory(tag_file_path: str) -> Dict[str, int]:
    result = dict()
    _LINE_RE = re.compile(r"^\s*(\d+) (.+)$")
    with open(tag_file_path, mode="r", encoding="utf-8") as reader:
        lines = reader.readlines()
        for idx, line in enumerate(lines):
            match = _LINE_RE.match(line)
            if match:
                result[match.group(2)] = int(match.group(1))
            else:
                print(f"!! LINE {idx}: No match")
    return result


def track_hits(inventory: Dict[str, int], regex_targets: Dict[int, Any]):
    report = defaultdict(lambda: {"total_count": 0, "distinct": 0})
    pattern_hits = defaultdict(lambda: [])
    missing = []

    # Loop over inventory, logging hits and missed items
    for tag, count in inventory.items():
        found_match = False
        for line_num, regex in regex_targets.items():
            if regex.match(tag):
                if not found_match:
                    found_match = True

                pattern_hits[tag].append(regex.pattern)
                report[line_num]["distinct"] += 1
                report[line_num]["total_count"] += count

        if not found_match:
            missing.append(tag)
    return report, missing, pattern_hits


def main(regex_file_path: str, tag_file_path: str):
    # Parse regex file
    regex_targets = parse_regex_targets(regex_file_path)

    # Parse inventory file
    inventory = parse_inventory(tag_file_path)

    # Track regex hits against inventory
    reports, missing, hits = track_hits(inventory, regex_targets)

    ranked_reports = sorted(
        reports.items(), key=lambda t: t[1]["total_count"], reverse=True
    )

    total_occurrences = sum([count for count in inventory.values()])
    # Report
    print(f"{total_occurrences} matches for {len(regex_targets)} regular expressions")

    duplicates = []
    total_dups = 0
    for tag, pat_lst in hits.items():
        if len(pat_lst) > 1:
            # duplicates[tag] = pat_lst
            duplicates.append((tag, pat_lst))
            total_dups += inventory[tag] * (len(pat_lst) - 1)

    print(f"{len(duplicates)} tags match >1 regex pattern. Examples:")

    for tag, pat_lst in duplicates[0:10]:
        print(f"{tag:30} {", ".join(pat_lst[0:5]):40}")
    # print(f"{'regex':30} {'distinct hits':>9} {'total hits':>12}")

    total_missing = sum([inventory[tag] for tag in missing])
    print(f"\n{len(missing)} missed tags. Preview:")
    for tag in missing[0:10]:
        print(f"{tag:30} {inventory[tag]:>9}")

    print(f"Total occurrences remaining: {total_missing}")
    running = 0
    for _, report in ranked_reports:
        running += report["total_count"]

    print(
        f"\nCOVERAGE: {(running - total_dups) / total_occurrences * 100:.4f}% OF ALL OCCURRENCES"
    )
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--regex", required=True)
    parser.add_argument("--tags", required=True)
    args = parser.parse_args()
    main(args.regex, args.tags)
