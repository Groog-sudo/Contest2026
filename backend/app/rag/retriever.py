def retrieve_context(question: str, top_k: int = 3) -> list[dict[str, str | float]]:
    return [
        {
            "id": "stub-context",
            "title": f"Relevant context for '{question[:30]}'",
            "score": max(0.1, 1 - (top_k * 0.05)),
        }
    ]

