from pydantic import BaseModel


class SendEmailRequest(BaseModel):
    institution_id: int
    response_code: str | None = None
    attach_samples: bool = False