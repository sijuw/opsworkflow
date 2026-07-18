import os
from datetime import datetime

# Moved the import above the other FastAPI imports for standard formatting
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
from app.schemas.email_preview import (
    EmailPreviewRequest,
    EmailPreviewResponse,
)

SMTP_USERNAME = os.getenv("SMTP_USERNAME")

router = APIRouter(prefix="/email", tags=["Email"])

@router.post("/preview", response_model=EmailPreviewResponse)
def preview_email(
    request: EmailPreviewRequest,
    db: Session = Depends(get_db),
    transaction_db: Session = Depends(get_transaction_db),
):
    # 1. Fetch the institution
    institution = get_institution(db, request.institution_id)

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    # 2. Fetch the samples to get the count and latest transaction time
    samples = get_sample_transactions(
        transaction_db,
        institution.bank_id,
        request.response_code,
    )

    sample_count = len(samples)
    latest_transaction = samples[0].request_time if samples else None

    # 3. Calculate the attachment name if the user requested samples
    attachment_name = None
    if request.attach_samples:
        today_str = datetime.now().strftime("%Y%m%d")
        rc_str = request.response_code or "N/A"
        attachment_name = (
            f"{institution.name.replace(' ', '_')}"
            f"_RC{rc_str}_{today_str}.xlsx"
        )

    # 4. Return the populated response
    return EmailPreviewResponse(
        attachment_name=attachment_name,
        sample_count=sample_count,
        latest_transaction=latest_transaction,
    )


@router.post("/send")
def send_email(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
    transaction_db: Session = Depends(get_transaction_db)
):
    # 1. Fetch Institution
    institution = get_institution(db, request.institution_id)

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    # 2. Parse Email Addresses
    to = [email.strip() for email in institution.email_to.split(",")]

    cc = []
    if institution.email_cc:
        cc = [email.strip() for email in institution.email_cc.split(",")]

    # 3. Fetch Samples
    samples = get_sample_transactions(
        transaction_db,
        institution.bank_id,
        request.response_code,
    )

    sample_count = len(samples)
    latest_transaction = None

    if samples:
        latest_transaction = samples[0].request_time
        
    # 4. Define Common Variables
    today_str = datetime.now().strftime("%Y%m%d")
    rc_str = request.response_code or "N/A"
    
    # 5. Generate Attachment
    excel_file = None
    attachment_filename = (
        f"{institution.name.replace(' ', '_')}"
        f"_RC{rc_str}_{today_str}.xlsx"
    )
    
    if request.attach_samples:
        excel_file = generate_excel(
            samples,
            attachment_filename,
        )

    # 6. Format the Subject Line
    subject_line = f"{institution.name} | ATS | RC{rc_str} | {today_str}"

    # 7. Format Conditional Texts
    # Note: Added 'Additional Context:' inside the strong tags so it renders nicely
    comments_text = f"<br><br><strong>Additional Context:</strong><br>{request.comments}" if request.comments else ""
    attachment_text = "<br><br>Please find attached sample transactions for your investigation." if request.attach_samples else ""

    # 8. Format the Body using HTML
    body_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>Hello Team,</p>
            
            <p>Please be informed that {institution.name} bank card transactions are currently failing with RC{rc_str}.{comments_text}</p>
            
            <p>Kindly assist with the review.{attachment_text}</p>
            
            <br>
            <p>Thanks and warm regards,<br>
            <strong>Application Support Team</strong><br>
            Moniepoint</p>
        </body>
    </html>
    """

    # 9. Send the Email
    send_smtp_email(
        to=to,
        cc=cc,
        subject=subject_line,
        body=body_content,
        attachment_path=excel_file if request.attach_samples else None,
    )

    # 10. Cleanup
    if request.attach_samples and excel_file and os.path.exists(excel_file):
        os.remove(excel_file)

    return {
        "message": "Email sent successfully"
    }