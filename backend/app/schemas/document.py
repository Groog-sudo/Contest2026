from typing import Literal

from pydantic import BaseModel


class UploadDocumentResponse(BaseModel):
    document_id: str
    status: Literal["accepted", "knowledge_base_pending"]
