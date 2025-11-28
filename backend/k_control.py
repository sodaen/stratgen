def compute_k(slides: int | None, length: str | None, k_in: int | None) -> int:
    if isinstance(k_in, int):
        return max(1, min(5, k_in))
    s = int(slides or 0)
    if s >= 80: return 4
    if s >= 40: return 3
    return 2
