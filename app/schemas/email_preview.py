from datetime import datetime

from pydantic import BaseModel


class EmailPreviewRequest(BaseModel):
    institution_id: int
    response_code: str | None = None
    attach_samples: bool = False
    comments: str | None = None


class EmailPreviewResponse(BaseModel):
    subject: str
    to: list[str]
    cc: list[str]
    body: str

    attachment_name: str | None = None
    sample_count: int
    latest_transaction: datetime | None = None
