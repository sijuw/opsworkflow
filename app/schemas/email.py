from pydantic import BaseModel


class SendEmailRequest(BaseModel):
    institution_id: int
    response_code: str | None = None
    attach_samples: bool
    comments: str | None = None

class EmailPreviewResponse(BaseModel):
    subject: str
    institution: str
    response_code: str | None

    recipients: list[str]
    cc: list[str]

    attachment_name: str | None
    sample_count: int

    comments: str | None

    body: str