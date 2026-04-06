from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings


@dataclass
class StoredObject:
    key: str
    url: str
    size: int
    content_type: str


class ObjectStorageClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = settings.object_storage_provider

    def put_bytes(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        if self.provider == "local":
            return self._put_local(key=key, data=data, content_type=content_type)
        if self.provider == "s3":
            return self._put_s3(key=key, data=data, content_type=content_type)
        raise RuntimeError(f"Unsupported storage provider: {self.provider}")

    def get_bytes(self, *, key: str) -> bytes:
        if self.provider == "local":
            base = Path(self.settings.object_storage_local_dir).expanduser().resolve()
            file_path = (base / key).resolve()
            return file_path.read_bytes()
        if self.provider == "s3":
            return self._get_s3_bytes(key=key)
        raise RuntimeError(f"Unsupported storage provider: {self.provider}")

    def _put_local(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        base = Path(self.settings.object_storage_local_dir).expanduser().resolve()
        file_path = (base / key).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)

        url = self._public_url_for_local(key)
        return StoredObject(
            key=key,
            url=url,
            size=len(data),
            content_type=content_type,
        )

    def _public_url_for_local(self, key: str) -> str:
        base_url = self.settings.object_storage_public_base_url
        if base_url:
            normalized = base_url.rstrip("/")
            return f"{normalized}/{key}"
        return f"local://{key}"

    def _put_s3(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        if not self.settings.object_storage_bucket:
            raise RuntimeError("OBJECT_STORAGE_BUCKET is required for s3 storage provider.")

        client = self._s3_client()
        client.put_object(
            Bucket=self.settings.object_storage_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

        base_url = self.settings.object_storage_public_base_url
        if base_url:
            url = f"{base_url.rstrip('/')}/{key}"
        else:
            url = f"s3://{self.settings.object_storage_bucket}/{key}"

        return StoredObject(
            key=key,
            url=url,
            size=len(data),
            content_type=content_type,
        )

    def _get_s3_bytes(self, *, key: str) -> bytes:
        if not self.settings.object_storage_bucket:
            raise RuntimeError("OBJECT_STORAGE_BUCKET is required for s3 storage provider.")

        client = self._s3_client()
        response = client.get_object(Bucket=self.settings.object_storage_bucket, Key=key)
        body = response["Body"].read()
        return body

    def _s3_client(self):
        import boto3

        kwargs = {
            "service_name": "s3",
            "region_name": self.settings.object_storage_region,
            "aws_access_key_id": self.settings.object_storage_access_key,
            "aws_secret_access_key": self.settings.object_storage_secret_key,
        }
        if self.settings.object_storage_endpoint_url:
            kwargs["endpoint_url"] = self.settings.object_storage_endpoint_url
        return boto3.client(**kwargs)
