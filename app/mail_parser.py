"""MIME parser + OTP extractor."""
import re
from email import policy
from email.parser import BytesParser

OTP_PATTERNS = [
    re.compile(r"\b(\d{4,8})\b"),
    re.compile(r"\b([A-Z0-9]{4,8})\b"),
]


def parse_raw_mime(raw: bytes) -> dict:
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    to_addr = (msg.get("To") or "").strip()
    from_addr = (msg.get("From") or "").strip()
    subject = (msg.get("Subject") or "").strip()

    text_body, html_body = "", ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    text_body += part.get_content()
                except Exception:
                    pass
            elif ctype == "text/html":
                try:
                    html_body += part.get_content()
                except Exception:
                    pass
    else:
        ctype = msg.get_content_type()
        try:
            content = msg.get_content()
        except Exception:
            content = ""
        if ctype == "text/html":
            html_body = content
        else:
            text_body = content

    return {"to": to_addr, "from": from_addr, "subject": subject,
            "text": text_body, "html": html_body}


def extract_otp(text: str):
    if not text:
        return None
    for pat in OTP_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    m = re.search(r"<([^>]+)>", addr)
    if m:
        return m.group(1).strip().lower()
    return addr.strip().lower()
