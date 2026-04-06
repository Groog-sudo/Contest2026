from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_prefix: str = "/api/v1"
    app_db_path: str = Field(default="./data/mentoring.sqlite3", alias="APP_DB_PATH")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    openai_stt_model: str = Field(
        default="gpt-4o-mini-transcribe",
        alias="OPENAI_STT_MODEL",
    )
    openai_tts_model: str = Field(
        default="gpt-4o-mini-tts",
        alias="OPENAI_TTS_MODEL",
    )
    pinecone_api_key: str | None = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_index_name: str | None = Field(default=None, alias="PINECONE_INDEX_NAME")
    pinecone_namespace: str = Field(default="contest2026", alias="PINECONE_NAMESPACE")
    object_storage_provider: str = Field(default="local", alias="OBJECT_STORAGE_PROVIDER")
    object_storage_bucket: str | None = Field(default=None, alias="OBJECT_STORAGE_BUCKET")
    object_storage_region: str | None = Field(default=None, alias="OBJECT_STORAGE_REGION")
    object_storage_endpoint_url: str | None = Field(
        default=None,
        alias="OBJECT_STORAGE_ENDPOINT_URL",
    )
    object_storage_access_key: str | None = Field(
        default=None,
        alias="OBJECT_STORAGE_ACCESS_KEY",
    )
    object_storage_secret_key: str | None = Field(
        default=None,
        alias="OBJECT_STORAGE_SECRET_KEY",
    )
    object_storage_local_dir: str = Field(
        default="./data/object_storage",
        alias="OBJECT_STORAGE_LOCAL_DIR",
    )
    object_storage_public_base_url: str | None = Field(
        default=None,
        alias="OBJECT_STORAGE_PUBLIC_BASE_URL",
    )
    stt_provider_name: str = Field(default="mock", alias="STT_PROVIDER_NAME")
    stt_provider_api_key: str | None = Field(default=None, alias="STT_PROVIDER_API_KEY")
    tts_provider_name: str = Field(default="mock", alias="TTS_PROVIDER_NAME")
    tts_provider_api_key: str | None = Field(default=None, alias="TTS_PROVIDER_API_KEY")
    queue_auto_process: bool = Field(default=True, alias="QUEUE_AUTO_PROCESS")
    queue_max_attempts: int = Field(default=3, alias="QUEUE_MAX_ATTEMPTS")
    call_provider_name: str = Field(default="mock", alias="CALL_PROVIDER_NAME")
    call_provider_api_key: str | None = Field(default=None, alias="CALL_PROVIDER_API_KEY")
    outbound_call_from_number: str | None = Field(
        default=None,
        alias="OUTBOUND_CALL_FROM_NUMBER",
    )
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

    @property
    def outbound_call_configured(self) -> bool:
        return all(
            [
                bool(self.call_provider_name),
                bool(self.call_provider_api_key),
                bool(self.outbound_call_from_number),
            ]
        )

    @property
    def stt_configured(self) -> bool:
        return bool(self.stt_provider_name)

    @property
    def tts_configured(self) -> bool:
        return bool(self.tts_provider_name)

    @property
    def object_storage_configured(self) -> bool:
        if self.object_storage_provider == "local":
            return True
        if self.object_storage_provider == "s3":
            return bool(self.object_storage_bucket)
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
