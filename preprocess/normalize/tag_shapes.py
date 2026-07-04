from collections import defaultdict
import argparse
import re
from typing import List, Tuple

def parse_file(file: str) -> List[Tuple]:
    result = []
    _LINE_RE = re.compile(r"^\s*(\d+) (.+)$")
    with open(file, mode="r", encoding="utf-8") as reader:
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

def cluster_tags(tag_counts: list) -> defaultdict:
    """Normalize tags, reducing them to clusters"""
    reports = defaultdict(
        lambda: {"examples": [], "distinct": 0, "total_count": 0}
    )

    _DIGIT_RE = re.compile(r"\d")
    _WHITESPACE_RE = re.compile(r"\s")
    for tag, count in tag_counts:
        normalized_tag = tag.lower() # convert everything to lower case
        normalized_tag = _DIGIT_RE.sub("0", normalized_tag) # substitute digits with placeholder
        normalized_tag = _WHITESPACE_RE.sub(" ", normalized_tag) # normalize all whitespace

        # Accumulate reduced form tag and counts
        reports[normalized_tag]["distinct"] += 1
        reports[normalized_tag]["total_count"] += count
        if len(reports[normalized_tag]["examples"]) < 5:
            reports[normalized_tag]["examples"].append(tag)
    return reports

def main(file: str):
    # Read file and parse contents
    tag_counts = parse_file(file)

    # Accumulate string tag 'clusters' by normalizing tags
    clusters = cluster_tags(tag_counts)
    
    # Rank by total count to log on console?
    ranked_clusters = sorted(
        clusters.items(),
        key=lambda t: t[1]["total_count"],
        reverse=True
    )

    # Total distinct tags
    total_tags = sum([t["distinct"] for _, t in clusters.items()])

    # Total occurrences
    total_occurrences = sum([t["total_count"] for _, t in clusters.items()])
    
    print(f"Total distinct tags: {total_tags}; Total occurrences: {total_occurrences}; {len(clusters)} normalized tags")
    
    # input("Ready for full report?")
    # Report findings: how many clusters cover 90% of occurrences? 
    running = 0
    first_cutoff_line_written = False 
    second_cutoff_line_written = False

    print(f"{'shape'}\t{'distinct'}\t{'occurrences'}\texamples")

    for cluster_key, cluster_report in ranked_clusters:
        examples = ", ".join(cluster_report["examples"])

        print(f"{cluster_key}\t{cluster_report["distinct"]}\t{cluster_report["total_count"]}\t{examples}")
        running += cluster_report["total_count"]
        pct = running / total_occurrences

        if pct >= 0.9 and running - cluster_report["total_count"] < total_occurrences * 0.90 and not first_cutoff_line_written:
            print(f"{"-" * 30} 90% DATA COVERED ABOVE THIS LINE {"-" * 30}")
            first_cutoff_line_written = True
        
        if pct > 0.99 and not second_cutoff_line_written:
            print(f"{"-" * 30} 99% DATA COVERED ABOVE THIS LINE {"-" * 30}")
            second_cutoff_line_written = True
    # Write all to file if save
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Tag count inventory file")
    args = parser.parse_args()
    main(args.file)