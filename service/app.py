import smtplib
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import logging


from schemas.user import Email_Schema
load_dotenv()

logger = logging.getLogger(__name__)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SENDER = os.getenv("SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(to: list[str], subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = ", ".join(to)
    msg.set_content(body)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        logger.info(e)