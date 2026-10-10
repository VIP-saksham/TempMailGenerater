import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .config import settings
from .db import Base


def _uuid():
    return uuid.uuid4().hex


def _expiry():
    return datetime.utcnow() + timedelta(hours=settings.mail_ttl_hours)


class MailInbox(Base):
    __tablename__ = "mail_inboxes"

    id = Column(String, primary_key=True, default=_uuid)
    address = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=_expiry)

    messages = relationship(
        "MailMessage", back_populates="inbox",
        cascade="all, delete-orphan",
    )


class MailMessage(Base):
    __tablename__ = "mail_messages"

    id = Column(String, primary_key=True, default=_uuid)
    inbox_id = Column(String, ForeignKey("mail_inboxes.id"), nullable=False, index=True)
    sender = Column(String, nullable=False, default="")
    subject = Column(String, default="")
    body_text = Column(Text, default="")
    body_html = Column(Text, default="")
    received_at = Column(DateTime, default=datetime.utcnow)

    inbox = relationship("MailInbox", back_populates="messages")
