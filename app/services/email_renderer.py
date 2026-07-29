import html
from dataclasses import dataclass, field
from datetime import datetime

from app.models.institution import Institution


@dataclass
class RenderedEmail:
    """The one description of an outgoing notification.

    Both /email/preview and /email/send build this, so what an engineer
    approves in the dialog is the same object that reaches the recipient.
    """

    subject: str
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    body: str = ""
    attachment_name: str | None = None


def _split_emails(value: str | None) -> list[str]:
    if not value:
        return []

    return [email.strip() for email in value.split(",") if email.strip()]


def render_email(
    institution: Institution,
    response_code: str | None,
    comments: str | None,
    attach_samples: bool,
    now: datetime | None = None,
) -> RenderedEmail:
    now = now or datetime.now()
    today_str = now.strftime("%Y%m%d")

    rc_part = f"_RC{response_code}" if response_code else ""
    subject_rc = f" | RC{response_code}" if response_code else ""
    body_rc = f" with RC{response_code}" if response_code else ""

    attachment_name = None
    if attach_samples:
        attachment_name = (
            f"{institution.name.replace(' ', '_')}"
            f"{rc_part}_{today_str}.xlsx"
        )

    # Institution names and comments are free text landing in an HTML
    # document, so escape both before interpolating.
    safe_name = html.escape(institution.name)

    comments_text = ""
    if comments:
        comments_text = (
            "<br><br><strong>Additional Context:</strong><br>"
            f"{html.escape(comments)}"
        )

    attachment_text = ""
    if attach_samples:
        attachment_text = (
            "<br><br>Please find attached sample transactions "
            "for your investigation."
        )

    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>Hello Team,</p>

            <p>Please be informed that {safe_name} bank card transactions are currently failing{body_rc}.{comments_text}</p>

            <p>Kindly assist with the review.{attachment_text}</p>

            <br>
            <p>Thanks and warm regards,</p>
            <p><strong>Application Support Team</strong></p>
        </body>
    </html>
    """

    return RenderedEmail(
        subject=f"{institution.name} | ATS{subject_rc} | {today_str}",
        to=_split_emails(institution.email_to),
        cc=_split_emails(institution.email_cc),
        body=body,
        attachment_name=attachment_name,
    )
