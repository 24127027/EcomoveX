from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from utils.config import settings


class EmailAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SEND_GRID_API_KEY
        if not self.api_key:
            raise ValueError("SendGrid API key is required")

        self.from_email = settings.SMTP_USER
        if not self.from_email:
            raise ValueError("SMTP_USER (sender email) is required")

        self.client = SendGridAPIClient(self.api_key)

    async def send_email(
        self, to_email: str, subject: str, content: str, content_type: str = "plain"
    ) -> bool:
        try:
            # Convert plain text to HTML if needed
            html_content = (
                content if content_type == "html" else f"<pre>{content}</pre>"
            )

            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )

            response = self.client.send(message)

            if response.status_code in (200, 202):
                return True
            else:
                print(
                    f"[ERROR] SendGrid returned status {response.status_code} for {to_email}"
                )
                raise Exception(f"SendGrid failed with status {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Failed to send email to {to_email}: {e}")
            raise
