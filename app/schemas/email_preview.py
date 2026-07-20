from pydantic import BaseModel

from typing import Optional
from datetime import datetime
class EmailPreviewRequest(BaseModel):
    institution_id: int
    response_code: str | None = None
    attach_samples: bool = False


class EmailPreviewResponse(BaseModel):
    attachment_name: str | None = None
    sample_count: int
    latest_transaction: datetime | None = None