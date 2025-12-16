import aiosmtplib
from email.message import EmailMessage
from utils.config import settings

async def send_email(to_email: str, subject: str, content: str, content_type: str = "plain") -> bool:
    try:
        message = EmailMessage()
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        
        if content_type == "html":
            message.add_alternative(content, subtype="html")
        else:
            message.set_content(content)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=settings.SMTP_USE_TLS,
            start_tls=settings.SMTP_STARTTLS,
            timeout=settings.SMTP_TIMEOUT
        )
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")
        raise