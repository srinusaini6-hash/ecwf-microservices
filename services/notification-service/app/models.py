from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient: Mapped[str] = mapped_column(String(255))
    actual_recipient: Mapped[str] = mapped_column(String(255))
    template: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
