import pandas as pd
import json
import gzip
from tqdm import tqdm

TERMINAL_PUNCTUATION = {
    "᪩",
    "？",
    "⁈",
    "𑩂",
    "．",
    "꩞",
    "𑅃",
    "﹗",
    "𑂾",
    "\u1b7d",
    "፧",
    "𑅂",
    "꡶",
    "꘎",
    "⁉",
    "࠾",
    "᪨",
    "𑊩",
    "𑱂",
    "᱿",
    "𖩮",
    "᥅",
    "\U00011f43",
    "\U00011f44",
    "﹒",
    "𑈹",
    "𑈸",
    "።",
    "܂",
    "؞",
    "꛳",
    "\U00010f88",
    "𑗍",
    "𐩖",
    "𑙂",
    "\u061d",
    "꩟",
    "᠉",
    "\u1b7e",
    "𑗗",
    "᰼",
    "𑻸",
    "؟",
    "𑪜",
    "꧉",
    "𑗉",
    "𐽙",
    "𖫵",
    "𖬷",
    "܀",
    "꓿",
    "᜵",
    "𑗏",
    "𑁇",
    "𑗓",
    "𑥄",
    "៖",
    "𑥆",
    "𑗑",
    "𑗒",
    "꯫",
    "۔",
    "𐩗",
    "\U00010f86",
    "꡷",
    "\u2e54",
    "｡",
    "៕",
    "߹",
    "⸮",
    ".",
    "𑇅",
    "࠹",
    "𛲟",
    "꫰",
    "꤯",
    "𐽗",
    "᭞",
    "𑜼",
    "፨",
    "𑃁",
    "꣏",
    "𑇟",
    "𖬸",
    "𑪛",
    "𑜾",
    "࠷",
    "𝪈",
    "?",
    "𑃀",
    "𑗃",
    "！",
    "։",
    "꣎",
    "॥",
    "𑗖",
    "᭛",
    "᠃",
    "!",
    "၊",
    "𖺘",
    "⁇",
    "𑗌",
    "𑑋",
    "𖭄",
    "᭟",
    "𑅁",
    "𑙁",
    "⸼",
    "꩝",
    "𑗋",
    "。",
    "꧈",
    "꫱",
    "𑜽",
    "𐽖",
    "𑂿",
    "᙮",
    "។",
    "꛷",
    "\U00010f89",
    "៚",
    "᥄",
    "𑗕",
    "𑗎",
    "᪪",
    "᭚",
    "࠽",
    "𑇞",
    "𑗊",
    "𐽘",
    "\u2e53",
    "𑗔",
    "𖩯",
    "𑇍",
    "𑻷",
    "𐽕",
    "𑩃",
    "।",
    "𑗂",
    "𑇆",
    "𑁈",
    "။",
    "᱾",
    "𑱁",
    "꘏",
    "܁",
    "᜶",
    "‼",
    "𑈻",
    "‽",
    "᪫",
    "﹖",
    "𑑌",
    "𑈼",
    "\U00010f87",
    "𑗐",
    "៙",
    "᰻",
}

STOP_CHARS = tuple(TERMINAL_PUNCTUATION)
# Store corpus attributes
results = {
    "glowbe": {},
    "ice": {}
}

# Stream leu_data
with gzip.open("output/preprocess/leu_data.jsonl.gz", "rt") as leu_gz:
    for line_num, doc_line in enumerate(tqdm(leu_gz), 1):
        try:
            doc = json.loads(doc_line)
        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error at line {line_num}: {e}")
            continue

        doc_id = doc.get("id")
        # Extract source from doc ID
        doc_source = doc_id.split("_")[0]

        if doc_source == "lince":
            continue
        # Split text by newline
        doc_lines = doc.get("text").split("\n")
        doc_lines = [line for line in doc_lines if line.strip() != ""]

        if len(doc_lines) != 0:
            # Sum up lines that end with TERMINAL PUNCTUATION
            doc_punct_lines = sum(1 for line in doc_lines if line.endswith(STOP_CHARS)) 

            # Store per doc result
            results[doc_source][doc_id] = {
                "lines": len(doc_lines),
                "punct_lines": doc_punct_lines,
                "line_punct_ratio": doc_punct_lines / len(doc_lines),
                "empty": False
            }
        else:
            # Store per doc result
            results[doc_source][doc_id] = {
                "lines": 0,
                "punct_lines": None,
                "line_punct_ratio": None,
                "empty": True
            }            

print("#"*30)

# Print source line stats
for source in results:
    print(f"results for {source}".upper())
    curr = pd.DataFrame.from_dict(results[source], orient='index')
    print(f"Empty documents: {curr["empty"].sum()}")

    # Print totals
    print(curr.lines.describe().apply("{0:.5f}".format))
    print(curr.line_punct_ratio.describe().apply("{0:.5f}".format))
    print()

print("Done")