import os
import smtplib

from email.message import EmailMessage


SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_smtp_email(
    to: list[str],
    cc: list[str],
    subject: str,
    body: str,
    attachment_path: str | None = None,
):
    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = SMTP_USERNAME
    message["To"] = ", ".join(to)

    if cc:
        message["Cc"] = ", ".join(cc)

    message.set_content(body)
    message.add_alternative(body, subtype="html")

    if attachment_path:
        with open(attachment_path, "rb") as file:
            message.add_attachment(
                file.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(attachment_path),
            )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)