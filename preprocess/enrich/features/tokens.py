from transformers import AutoTokenizer

MAX_TOKEN_LENGTH = 8192
tokenizer = AutoTokenizer.from_pretrained("allenai/dolma2-tokenizer")

def get_count(text: str) -> int:
    tokens = len(tokenizer.encode(text, truncation=True, max_length=MAX_TOKEN_LENGTH))
    truncated = tokens == MAX_TOKEN_LENGTH
    return tokens, truncated
