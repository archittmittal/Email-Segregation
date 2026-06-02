from __future__ import annotations
import re


def _clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip().rstrip(',').rstrip('.').strip()


def _extract_account(text: str) -> str | None:
    m = re.search(
        r'(?:ACCOUNT|ACC(?:OUNT)?|A/C)\s*:?\s*([\w\s&.,]+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if m:
        val = _clean(m.group(1))
        if 3 < len(val) < 80:
            return val
    return None


def _extract_delivery_port(text: str) -> str | None:
    patterns = [
        r'(?:DELIVERY|DELY)\s+(?:TO\s+MAKE\s+|TM\s+)?([A-Z][A-Z\s(),/.-]{2,60}?)(?:\n|LC|LAYCAN|REDELIVERY|REDEL|DURATION|$)',
        r'DELIVERY\s*:\s*([^\n]{3,60})',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            # Strip trailing noise
            val = re.sub(r'\s+(?:LC|LAYCAN|REDEL|DURATION|$).*', '', val, flags=re.IGNORECASE).strip()
            if 2 < len(val) < 80:
                return val
    return None


def _extract_redelivery_port(text: str) -> str | None:
    patterns = [
        r'(?:REDELIVERY|REDEL)\s*:?\s*([A-Z][A-Z\s(),/.-]{2,60}?)(?:\n|DURATION|3\.?\d+\s*%|$)',
        r'REDELIVERY\s*:\s*([^\n]{3,60})',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            if 2 < len(val) < 80:
                return val
    return None


def _extract_duration(text: str) -> str | None:
    patterns = [
        r'DURATION\s+(?:ABT\s+)?([\d\s\-–]+(?:DAYS?|MONTHS?|YEARS?)\s*(?:WOG)?)',
        r'(?:ABT\s+)?([\d]+\s*[-–]\s*[\d]+\s*(?:DAYS?|MONTHS?))\s*(?:WOG)?',
        r'(1[-–]\d+\s*YEARS?)',
        r'(\d+\s*(?:DAYS?|MONTHS?|YEARS?))',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            if len(val) > 1:
                return val
    return None


def _extract_laycan(text: str) -> str | None:
    patterns = [
        r'(?:LAYCAN|LC)\s*:?\s*([^\n]{3,40})',
        r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|JULY|AUG|SEP|OCT|NOV|DEC)\w*(?:\s+\d{4})?)',
        r'((?:MID|EARLY|LATE|FULL|END)\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|JULY|AUG|SEP|OCT|NOV|DEC)\w*(?:\s+\d{4})?)',
        r'(?:^|\n)(\d{1,2}\s*[-–]?\s*\d{1,2}(?:ST|ND|RD|TH)?\s+(?:JUN|JUNE|JUL|JULY|AUG|MAY)\w*(?:\s+\d{4})?)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = _clean(m.group(1))
            if 2 < len(val) < 60:
                return val
    return None


def _extract_cargo_name(text: str) -> str | None:
    # "1 TCT WITH GRAINS", "1 TCT WITH CLINKER TO BDESH"
    m = re.search(r'1\s*TCT\s+WITH\s+([A-Z][A-Z\s/]{2,30}?)(?:\n|TO\s|$)', text, re.IGNORECASE)
    if m:
        return _clean(m.group(1))
    # "CARGO: COAL"
    m = re.search(r'CARGO\s*:?\s*([A-Z][A-Z\s]{2,30}?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        return _clean(m.group(1))
    # Detect known commodities
    commodities = [
        'GRAIN', 'GRAINS', 'COAL', 'CLINKER', 'IRON ORE', 'FERTILIZER',
        'STEEL', 'STEELS', 'GENERAL CARGO', 'LAWFULS', 'GENS', 'LOGS',
        'BAUXITE', 'CEMENT', 'PHOSPHATE', 'SCRAPS', 'SOYBEANS',
    ]
    text_up = text.upper()
    for c in commodities:
        if c in text_up:
            return c
    return None


def _extract_cargo_type(text: str) -> str:
    text_up = text.upper()
    if any(x in text_up for x in ['STEEL', 'GENS', 'GENERAL CARGO', 'LAWFUL']):
        return 'BREAKBULK/GENERAL'
    if any(x in text_up for x in ['GRAIN', 'COAL', 'CLINKER', 'BAUXITE', 'IRON ORE']):
        return 'BULK'
    return 'BULK'


# ── Multi-cargo splitter ──────────────────────────────────────────────────────

def extract_cargo_tc(text: str, email_id: int) -> list[dict]:
    """Return list of TC cargo dicts extracted from email text."""
    results = []

    # Split on separators like ---...--- or +++...+++
    chunks = re.split(r'[-]{15,}|[+]{10,}', text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        chunk_up = chunk.upper()

        tc_signals = ['TCT', 'DELIVERY', 'DELY', 'REDELIVERY', 'REDEL', 'DURATION', 'TIME CHARTER']
        if not any(s in chunk_up for s in tc_signals):
            continue

        delivery = _extract_delivery_port(chunk)
        redelivery = _extract_redelivery_port(chunk)
        duration = _extract_duration(chunk)
        laycan = _extract_laycan(chunk)
        cargo_name = _extract_cargo_name(chunk)

        if delivery or redelivery or duration:
            results.append({
                'email_id': email_id,
                'account_name': _extract_account(chunk) or _extract_account(text),
                'cargo_name': cargo_name,
                'delivery_port': delivery,
                'redelivery_port': redelivery,
                'duration': duration,
                'laycan': laycan,
                'cargo_type': _extract_cargo_type(chunk),
            })

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        key = (r.get('delivery_port', ''), r.get('redelivery_port', ''), r.get('duration', ''))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique if unique else []
