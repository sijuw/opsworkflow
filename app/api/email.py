import os

SMTP_USERNAME = os.getenv("SMTP_USERNAME")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.institution import Institution
from app.schemas.email import SendEmailRequest
from app.services.email_service import get_institution
from app.db.transaction_dependencies import get_transaction_db
from app.services.transaction_service import get_sample_transactions
from app.services.excel_service import generate_excel
from app.services.smtp_service import send_smtp_email


router = APIRouter(prefix="/email", tags=["Email"])


@router.post("/send")
def send_email(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
    transaction_db: Session = Depends(get_transaction_db)
):
    institution = get_institution(db, request.institution_id)

    to = [email.strip() for email in institution.email_to.split(",")]

    cc = []
    if institution.email_cc:
        cc = [email.strip() for email in institution.email_cc.split(",")]

    samples = get_sample_transactions(
    transaction_db,
    institution.bank_id,
    request.response_code,
)
    excel_file = generate_excel(
    samples,
    institution.name,
    request.response_code,
)

    send_smtp_email(
    to=to,
    cc=cc,
    subject=f"{institution.name} Transaction Failure Notification",
    body=f"""
    Dear Team,

    Kindly be informed that we are currently observing transaction failures to {institution.name}.

    Response Code: {request.response_code or "N/A"}

    Please find attached sample transactions for your investigation.

    Regards,
    Application Support
    """,
    attachment_path=excel_file if request.attach_samples else None,
)

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    return {
    "message": "Email sent successfully"
}

    