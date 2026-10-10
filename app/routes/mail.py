"""temp mail endpoints — unlimited inboxes, apne domain pe, apne VPS pe.

    POST   /mail/inbox                      → naya inbox banao (optional custom local-part)
    GET    /mail/inbox/{inbox_id}           → inbox info
    GET    /mail/inbox/{inbox_id}/messages  → messages (OTP auto-extract)
    DELETE /mail/inbox/{inbox_id}           → inbox delete

    POST   /mail/ingest/raw                 → raw MIME (cloudflare worker se aata hai)
    GET    /mail/stats                      → pool stats
"""
import os
import re
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import MailInbox, MailMessage
from ..schemas import InboxOut, MailMessageOut, InboxCreate
from ..mail_parser import parse_raw_mime, extract_otp, normalize_address

router = APIRouter(prefix="/mail", tags=["mail"])

ALPHABET = string.ascii_lowercase + string.digits
MAX_INBOXES = 500  # safety cap — delete purane to naya banao


def gen_local_part(length: int = 10) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def pick_unique_address(db: Session, local_part: str | None = None) -> str:
    if local_part:
        lp = re.sub(r"[^a-z0-9\.\-\_]", "", local_part.lower().strip())
        if not lp or len(lp) > 40:
            raise HTTPException(400, "invalid local_part (a-z 0-9 . - _ only, max 40)")
        addr = f"{lp}@{settings.mail_domain}"
        if db.query(MailInbox).filter(MailInbox.address == addr).first():
            raise HTTPException(409, "that address is already taken — pick another")
        return addr
    for _ in range(10):
        addr = f"{gen_local_part()}@{settings.mail_domain}"
        if not db.query(MailInbox).filter(MailInbox.address == addr).first():
            return addr
    raise HTTPException(500, "could not allocate address")


def require_ingest_key(x_ingest_key: str = Header(default="")):
    expected = os.getenv("INGEST_KEY", "")
    if expected and x_ingest_key != expected:
        raise HTTPException(401, "invalid ingest key")
    return True


def _inbox_count(db: Session) -> int:
    return db.query(MailInbox).count()


@router.post("/inbox", response_model=InboxOut)
def create_inbox(payload: InboxCreate | None = None, db: Session = Depends(get_db)):
    if _inbox_count(db) >= MAX_INBOXES:
        raise HTTPException(429, "inbox limit reached — delete old inboxes first")
    local_part = payload.local_part if payload else None
    addr = pick_unique_address(db, local_part)
    inbox = MailInbox(address=addr)
    db.add(inbox)
    db.commit()
    db.refresh(inbox)
    return inbox


@router.get("/inbox/{inbox_id}", response_model=InboxOut)
def get_inbox(inbox_id: str, db: Session = Depends(get_db)):
    inbox = db.query(MailInbox).filter(MailInbox.id == inbox_id).first()
    if not inbox:
        raise HTTPException(404, "inbox not found")
    return inbox


@router.get("/inbox/{inbox_id}/messages", response_model=list[MailMessageOut])
def list_messages(inbox_id: str, db: Session = Depends(get_db)):
    inbox = db.query(MailInbox).filter(MailInbox.id == inbox_id).first()
    if not inbox:
        raise HTTPException(404, "inbox not found")
    out = []
    for m in sorted(inbox.messages, key=lambda x: x.received_at, reverse=True):
        otp = extract_otp(m.body_text or m.body_html or "")
        mo = MailMessageOut.model_validate(m)
        mo.otp = otp
        out.append(mo)
    return out


@router.delete("/inbox/{inbox_id}")
def delete_inbox(inbox_id: str, db: Session = Depends(get_db)):
    inbox = db.query(MailInbox).filter(MailInbox.id == inbox_id).first()
    if not inbox:
        raise HTTPException(404, "inbox not found")
    db.delete(inbox)
    db.commit()
    return {"ok": True}


@router.post("/ingest/raw", dependencies=[Depends(require_ingest_key)])
async def ingest_raw(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    parsed = parse_raw_mime(raw)
    to_addr = normalize_address(parsed["to"])
    if not to_addr:
        raise HTTPException(400, "no recipient")
    inbox = db.query(MailInbox).filter(MailInbox.address == to_addr).first()
    if not inbox:
        return {"ok": True, "stored": False, "reason": "no matching inbox"}
    msg = MailMessage(
        inbox_id=inbox.id,
        sender=normalize_address(parsed["from"]),
        subject=parsed["subject"][:500],
        body_text=parsed["text"] or "",
        body_html=parsed["html"] or "",
    )
    db.add(msg)
    db.commit()
    return {"ok": True, "stored": True, "message_id": msg.id}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    inboxes = _inbox_count(db)
    msgs = db.query(MailMessage).count()
    return {"inboxes": inboxes, "messages": msgs, "domain": settings.mail_domain}
