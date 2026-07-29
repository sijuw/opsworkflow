import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_token
from app.db.dependencies import get_db
from app.db.transaction_dependencies import get_transaction_db
from app.schemas.email import SendEmailRequest
from app.schemas.email_preview import (
    EmailPreviewRequest,
    EmailPreviewResponse,
)
from app.services.email_renderer import render_email
from app.services.email_service import get_institution
from app.services.excel_service import generate_excel
from app.services.smtp_service import send_smtp_email
from app.services.transaction_service import get_sample_transactions

router = APIRouter(
    prefix="/email",
    tags=["Email"],
    dependencies=[Depends(require_api_token)],
)


def _resolve_request(db, transaction_db, request):
    """Shared setup for preview and send: institution plus any samples."""
    institution = get_institution(db, request.institution_id)

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found",
        )

    samples = []
    if request.attach_samples:
        samples = get_sample_transactions(
            transaction_db,
            institution.bank_id,
            request.response_code,
        )

    return institution, samples


@router.post("/preview", response_model=EmailPreviewResponse)
def preview_email(
    request: EmailPreviewRequest,
    db: Session = Depends(get_db),
    transaction_db: Session = Depends(get_transaction_db),
):
    institution, samples = _resolve_request(db, transaction_db, request)

    rendered = render_email(
        institution=institution,
        response_code=request.response_code,
        comments=request.comments,
        attach_samples=request.attach_samples,
    )

    return EmailPreviewResponse(
        subject=rendered.subject,
        to=rendered.to,
        cc=rendered.cc,
        body=rendered.body,
        attachment_name=rendered.attachment_name,
        sample_count=len(samples),
        latest_transaction=samples[0].request_time if samples else None,
    )


@router.post("/send")
def send_email(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
    transaction_db: Session = Depends(get_transaction_db),
):
    institution, samples = _resolve_request(db, transaction_db, request)

    rendered = render_email(
        institution=institution,
        response_code=request.response_code,
        comments=request.comments,
        attach_samples=request.attach_samples,
    )

    excel_file = None
    if request.attach_samples and rendered.attachment_name:
        excel_file = generate_excel(samples, rendered.attachment_name)

    try:
        send_smtp_email(
            to=rendered.to,
            cc=rendered.cc,
            subject=rendered.subject,
            body=rendered.body,
            attachment_path=excel_file,
        )

    finally:
        # finally, so a failed send doesn't leave the report behind
        if excel_file and os.path.exists(excel_file):
            os.remove(excel_file)

    return {
        "message": "Email sent successfully"
    }
