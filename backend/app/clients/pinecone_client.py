from app.core.config import Settings


class PineconeClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_available(self) -> bool:
        return bool(self.settings.pinecone_api_key and self.settings.pinecone_index_name)

    def upsert_chunks(
        self,
        *,
        vectors: list[dict[str, object]],
        namespace: str | None = None,
    ) -> None:
        if not self.is_available() or not vectors:
            return

        index = self._index()
        index.upsert(vectors=vectors, namespace=namespace or self.settings.pinecone_namespace)

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        namespace: str | None = None,
    ) -> list[dict[str, object]]:
        if not self.is_available():
            return []

        index = self._index()
        response = index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace or self.settings.pinecone_namespace,
            include_metadata=True,
        )
        matches = getattr(response, "matches", []) or []
        items: list[dict[str, object]] = []
        for match in matches:
            metadata = getattr(match, "metadata", {}) or {}
            items.append(
                {
                    "id": getattr(match, "id", ""),
                    "score": getattr(match, "score", None),
                    "metadata": metadata,
                }
            )
        return items

    def _index(self):
        from pinecone import Pinecone

        client = Pinecone(api_key=self.settings.pinecone_api_key)
        return client.Index(self.settings.pinecone_index_name)
