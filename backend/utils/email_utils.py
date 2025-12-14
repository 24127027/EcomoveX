import aiosmtplib
from email.message import EmailMessage
from utils.config import settings

async def send_email(to_email: str, subject: str, content: str):
    try:
        print(f"[DEBUG] Preparing email to: {to_email}")
        message = EmailMessage()
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True
        )
        print(f"[INFO] Email sent to {to_email}")

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        raise e

