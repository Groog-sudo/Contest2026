from app.core.config import Settings


class PineconeClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_available(self) -> bool:
        return bool(self.settings.pinecone_api_key and self.settings.pinecone_index_name)

