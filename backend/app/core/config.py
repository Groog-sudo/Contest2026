from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_prefix: str = "/api/v1"
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    pinecone_api_key: str | None = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_index_name: str | None = Field(default=None, alias="PINECONE_INDEX_NAME")
    pinecone_namespace: str = Field(default="contest2026", alias="PINECONE_NAMESPACE")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def rag_configured(self) -> bool:
        return all(
            [
                bool(self.openai_api_key),
                bool(self.pinecone_api_key),
                bool(self.pinecone_index_name),
            ]
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

