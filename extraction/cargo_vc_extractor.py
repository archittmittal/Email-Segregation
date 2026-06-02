from __future__ import annotations
import re


def _clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip().rstrip(',').rstrip('.').strip()


def _extract_account(text: str) -> str | None:
    m = re.search(r'(?:ACCOUNT|ACC(?:OUNT)?|A/C)\s*:?\s*([\w\s&.,]+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        val = _clean(m.group(1))
        if 3 < len(val) < 80:
            return val
    m = re.search(r'@([\w-]+)\.', text)
    if m:
        return m.group(1).capitalize()
    return None


def _extract_quantity(text: str) -> str | None:
    # Matches: "15,000 - 20,000 MTS", "30000 MT", "55,000 MTS"
    m = re.search(
        r'([\d,]+\s*[-–]\s*[\d,]+\s*(?:MTS?|TONS?|MT)|[\d,]+\s*(?:MTS?|TONS?|MT))',
        text, re.IGNORECASE
    )
    if m:
        return _clean(m.group(1))
    return None


def _extract_cargo_name(text: str) -> str | None:
    # After quantity: "15,000 MTS MOLASSES", "30000 MT COAL"
    m = re.search(
        r'[\d,]+\s*(?:[-–]\s*[\d,]+\s*)?(?:\d+PCT\s*\w+\s*)?(?:MTS?|TONS?|MT)\s+'
        r'(?:OF\s+)?(?:\d+PCT\s*\w+\s*)?([A-Z][A-Z\s/]{2,40}?)(?:\s*\n|\s*(?:LOAD|LP|POL|IN\s+BULK|FIOS|$))',
        text, re.IGNORECASE
    )
    if m:
        val = _clean(m.group(1))
        if len(val) > 2:
            return val

    # Alternative: "CARGO: IRON ORE" or "CARGO OF COAL"
    m = re.search(r'CARGO\s*(?:OF\s*)?:?\s*([A-Z][A-Z\s]{2,30}?)(?:\n|LP|POL|LOAD|$)', text, re.IGNORECASE)
    if m:
        return _clean(m.group(1))

    # Slash format: port / port pattern — commodity may be in subject
    # Try common commodities
    commodities = [
        'COAL', 'GRAIN', 'IRON ORE', 'FERTILIZER', 'UREA', 'WHEAT', 'CORN',
        'SUGAR', 'RICE', 'CLINKER', 'CEMENT', 'BAUXITE', 'PHOSPHATE',
        'MOLASSES', 'SALT', 'SCRAP', 'STEEL', 'HRC', 'PET COKE', 'GYPSUM',
        'SOYBEANS', 'SOYBEAN MEAL', 'IRON SLAG', 'ROCK PHOSPHATE', 'LIMESTONE',
        'MOLOCHOPT', 'SULFUR', 'MOP'
    ]
    text_up = text.upper()
    for c in commodities:
        if c in text_up:
            return c

    return None


def _extract_loading_port(text: str) -> str | None:
    patterns = [
        r'(?:LOAD(?:ING)?\s*PORT|LP|POL)\s*:?\s*([A-Z][A-Z\s,/+&.()-]{2,60}?)(?:\n|DISCHARGE|DISCH|DP|POD|$)',
        r'(?:LOAD\s*PORT\s*:\s*)([^\n]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            if 2 < len(val) < 80:
                return val

    # Slash format: "JEDDAH / BILBAO" → first is load
    m = re.search(r'^([A-Z][A-Z\s,]{2,30}?)\s*/\s*([A-Z][A-Z\s,]{2,30})', text, re.IGNORECASE | re.MULTILINE)
    if m:
        return _clean(m.group(1))

    return None


def _extract_discharge_port(text: str) -> str | None:
    patterns = [
        r'(?:DISCH(?:ARGE)?\s*PORT|DP|POD)\s*:?\s*([A-Z][A-Z\s,/+&.()-]{2,80}?)(?:\n|LAYCAN|LOAD|LP|COMM|$)',
        r'(?:DISCHARGE\s*PORT\s*:\s*)([^\n]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            if 2 < len(val) < 80:
                return val

    # Slash format: "JEDDAH / BILBAO" → second is discharge
    m = re.search(r'^([A-Z][A-Z\s,]{2,30}?)\s*/\s*([A-Z][A-Z\s,]{2,30})', text, re.IGNORECASE | re.MULTILINE)
    if m:
        return _clean(m.group(2))

    return None


def _extract_laycan(text: str) -> str | None:
    patterns = [
        r'LAYCAN\s*:?\s*([^\n]{3,40})',
        r'(?:LC|L/C)\s*:?\s*([^\n]{3,30})',
        # Date range like "25 June - 5 July" or "25-30 july"
        r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|JULY|AUG|SEP|OCT|NOV|DEC)\w*(?:\s+\d{4})?)',
        r'(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|JULY|AUG|SEP|OCT|NOV|DEC)\w*\s*[-–]\s*\d{1,2}\s+\w+(?:\s+\d{4})?)',
        r'((?:MID|EARLY|LATE|END)\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|JULY|AUG|SEP|OCT|NOV|DEC)\w*(?:\s+\d{4})?)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = _clean(m.group(1))
            if 2 < len(val) < 60:
                return val
    return None


def _extract_cargo_type(text: str) -> str:
    text_up = text.upper()
    if 'IN BULK' in text_up:
        return 'BULK'
    if 'BAGGED' in text_up:
        return 'BAGGED'
    if 'CONTAINER' in text_up:
        return 'CONTAINERISED'
    return 'BULK'


# ── Multi-cargo splitter (for emails with several VC cargos separated by +++ or ---) ──

def extract_cargo_vc(text: str, email_id: int) -> list[dict]:
    """Return list of VC cargo dicts extracted from email text."""
    results = []

    # Split on separators like +++...+++ or ---...---
    chunks = re.split(r'[+]{10,}|[-]{20,}', text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # Only process chunks that look like VC cargo
        chunk_up = chunk.upper()
        vc_signals = ['LOAD PORT', 'LP:', 'POL', 'DISCHARGE PORT', 'DP:', 'POD', 'LAYCAN', 'MTS', 'MT ']
        if not any(s in chunk_up for s in vc_signals):
            continue

        qty = _extract_quantity(chunk)
        cargo_name = _extract_cargo_name(chunk)
        loading_port = _extract_loading_port(chunk)
        discharge_port = _extract_discharge_port(chunk)
        laycan = _extract_laycan(chunk)

        if loading_port or discharge_port or laycan:
            results.append({
                'email_id': email_id,
                'account_name': _extract_account(chunk) or _extract_account(text),
                'cargo_name': cargo_name,
                'loading_port': loading_port,
                'discharge_port': discharge_port,
                'laycan': laycan,
                'cargo_type': _extract_cargo_type(chunk),
                'quantity': qty,
            })

    # Deduplicate (same load+discharge)
    seen = set()
    unique = []
    for r in results:
        key = (r.get('loading_port', ''), r.get('discharge_port', ''))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique if unique else []
