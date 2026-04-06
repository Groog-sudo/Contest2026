def split_text(text: str, chunk_size: int = 500) -> list[str]:
    if not text:
        return []

    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]

