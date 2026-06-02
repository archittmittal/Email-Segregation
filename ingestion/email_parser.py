"""Lightweight email text normaliser + attachment parser — no external deps required."""
import re
import email as _email_lib
from email import policy as _policy


# ── Plain text / paste parser ─────────────────────────────────────────────────

def parse_email(raw: str) -> dict:
    """
    Accepts raw email text (paste or file content).
    Returns dict with: subject, sender, body (cleaned), received_at.
    """
    lines = raw.splitlines()
    subject = 'Manual Input'
    sender = 'unknown'
    received_at = None
    body_lines = []
    in_header = True

    for line in lines:
        stripped = line.strip()
        if in_header:
            if stripped.lower().startswith('subject:'):
                subject = stripped[8:].strip()
            elif stripped.lower().startswith('from:'):
                sender = stripped[5:].strip()
            elif stripped.lower().startswith('date:'):
                date_str = stripped[5:].strip()
                from email.utils import parsedate_to_datetime
                try:
                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    pass
            elif stripped == '':
                in_header = False
        else:
            body_lines.append(line)

    body = '\n'.join(body_lines) if body_lines else raw

    # Clean up excessive whitespace while preserving structure
    body = re.sub(r'\r\n', '\n', body)
    body = re.sub(r'\n{4,}', '\n\n\n', body)

    return {
        'subject': subject,
        'sender': sender,
        'body': body.strip(),
        'received_at': received_at,
    }


# ── EML parser (stdlib `email`) ────────────────────────────────────────────────

def parse_eml_bytes(raw_bytes: bytes) -> dict:
    """
    Parse a raw .eml file. Extracts subject, sender, received_at, and the plain-text body.
    Attachment text content is appended after the main body.
    Returns dict: {subject, sender, body, received_at, attachments: [{filename, text}]}
    """
    msg = _email_lib.message_from_bytes(raw_bytes, policy=_policy.default)

    subject = str(msg.get('Subject', 'No Subject'))
    sender  = str(msg.get('From', 'unknown'))
    
    received_at = None
    date_str = msg.get('Date')
    if date_str:
        from email.utils import parsedate_to_datetime
        try:
            received_at = parsedate_to_datetime(str(date_str))
        except Exception:
            pass

    body_parts = []
    attachments = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition  = str(part.get('Content-Disposition', ''))
        filename     = part.get_filename()

        if filename:
            # It's an attachment
            try:
                payload = part.get_payload(decode=True) or b''
                att_text = extract_text_from_attachment(filename, payload)
                if att_text:
                    attachments.append({'filename': filename, 'text': att_text})
                    body_parts.append(f'\n\n--- Attachment: {filename} ---\n{att_text}')
            except Exception:
                pass
        elif content_type == 'text/plain' and 'attachment' not in disposition:
            try:
                charset = part.get_content_charset() or 'utf-8'
                payload = part.get_payload(decode=True) or b''
                body_parts.append(payload.decode(charset, errors='replace'))
            except Exception:
                pass

    body = '\n'.join(body_parts).strip()
    body = re.sub(r'\n{4,}', '\n\n\n', body)

    return {
        'subject': subject,
        'sender': sender,
        'body': body,
        'received_at': received_at,
        'attachments': attachments,
    }


# ── Attachment text extractor ─────────────────────────────────────────────────

def extract_text_from_attachment(filename: str, data: bytes) -> str:
    """
    Extract plain text from an attachment payload.
    Supports: .txt, .csv, .pdf (via pdfminer.six if installed; regex fallback otherwise).
    """
    name_lower = (filename or '').lower()

    if name_lower.endswith(('.txt', '.csv')):
        return data.decode('utf-8', errors='replace')

    if name_lower.endswith('.pdf'):
        return _extract_pdf_text(data)

    # Try decoding unknown types as UTF-8 text
    try:
        return data.decode('utf-8', errors='replace')
    except Exception:
        return ''


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes. Uses pdfminer.six if available, else regex fallback."""
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        import io

        output = io.StringIO()
        extract_text_to_fp(io.BytesIO(data), output, laparams=LAParams())
        return output.getvalue().strip()
    except ImportError:
        pass

    # Regex fallback: extract printable text chunks from raw PDF bytes
    raw = data.decode('latin-1', errors='replace')
    chunks = re.findall(r'\(([^\)]{3,})\)', raw)
    return ' '.join(c for c in chunks if re.search(r'[a-zA-Z]{3,}', c)).strip()
