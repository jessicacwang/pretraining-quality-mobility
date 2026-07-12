def get_bucket(token_count: int) -> str:
    # 0-64
    if 0 <= token_count < 64:
        return "0-64"
    # 64-128
    elif 64 <= token_count < 128:
        return "64-128"
    # 128-256
    elif 128 <= token_count < 256:
        return "128-256"
    # 256-512
    elif 256 <= token_count < 512:
        return "256-512"
    # 512-1024
    elif 512 <= token_count < 1024:
        return "512-1024"
    # 1024-2048
    elif 1024 <= token_count < 2048:
        return "1024-2048"
    # 2048+
    elif token_count >= 2048:
        return "2048+"
