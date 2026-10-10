from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class InboxOut(BaseModel):
    id: str
    address: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class MailMessageOut(BaseModel):
    id: str
    sender: str
    subject: str
    body_text: str
    body_html: str
    received_at: datetime
    otp: Optional[str] = None

    class Config:
        from_attributes = True


class InboxCreate(BaseModel):
    # optional: user apni pasand ka local-part maang sakta hai
    local_part: Optional[str] = None
