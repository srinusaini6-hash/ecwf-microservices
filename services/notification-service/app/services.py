import smtplib
import time
from email.message import EmailMessage

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DeliveryLog


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def send(self, data):
        original = str(data.to)
        actual = settings.developer_redirect_email or original
        delivery_status = "skipped"
        error = None

        if settings.smtp_enabled and settings.smtp_host:
            for attempt in range(1, settings.notification_max_retries + 1):
                try:
                    message = EmailMessage()
                    from_address = settings.smtp_from_email or settings.email_from_address or settings.smtp_username
                    message["From"] = f"{settings.email_from_name} <{from_address}>" if settings.email_from_name and from_address else from_address
                    message["To"] = actual
                    message["Subject"] = data.subject
                    body = data.body
                    if settings.developer_redirect_email:
                        body = f"DEVELOPMENT REDIRECT\n\nOriginal recipient: {original}\nActual recipient: {actual}\n\n{body}"
                    message.set_content(body)
                    if settings.smtp_use_ssl:
                        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                            if settings.smtp_username:
                                server.login(settings.smtp_username, settings.smtp_password)
                            server.send_message(message)
                    else:
                        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                            if settings.smtp_use_tls:
                                server.starttls()
                            if settings.smtp_username:
                                server.login(settings.smtp_username, settings.smtp_password)
                            server.send_message(message)
                    delivery_status = "sent"
                    error = None
                    break
                except Exception as exc:
                    delivery_status = "failed"
                    error = str(exc)
                    if attempt < settings.notification_max_retries:
                        time.sleep(settings.notification_retry_delay_seconds)
        else:
            error = "SMTP is disabled or SMTP_HOST is missing."

        log = DeliveryLog(recipient=original, actual_recipient=actual, template=data.template, subject=data.subject, status=delivery_status, error=error)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)


        if delivery_status == "failed":
            raise HTTPException(502, {"message": "Email delivery failed.", "error": error})
        if delivery_status == "skipped":
            raise HTTPException(503, {"message": "Email delivery skipped.", "error": error})
        return {"delivery_id": log.id, "status": delivery_status, "recipient": original, "actual_recipient": actual}
