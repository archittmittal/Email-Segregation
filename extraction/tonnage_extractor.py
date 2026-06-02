from __future__ import annotations
import re


# ── Helper extractors ─────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip().rstrip(',').rstrip('.').strip()


def _extract_account(text: str) -> str | None:
    patterns = [
        r'(?:PRIME MARITIME)[^\n]*',
        r'(?:ACC(?:OUNT)?\s+)([\w\s]+?)(?:\n|$)',
        r'(?:FROM|ON\s+BEHALF\s+OF)\s*:?\s*([\w\s&.,]+?)(?:\n|$)',
        r'DEAR\s+SIRS[^\n]*\n.*?([A-Z][A-Z\s&.]+(?:INC|LTD|CO|CORP|SHIPPING|MARITIME)[^\n]*)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            grp = m.group(1) if m.lastindex else m.group(0)
            val = _clean(grp)
            if 3 < len(val) < 80:
                return val
    # Try extracting company from email domain
    m = re.search(r'@([\w-]+)\.', text)
    if m:
        return m.group(1).capitalize()
    return None


def _extract_flag(text: str) -> str | None:
    m = re.search(r'(?:FLAG\s*:?\s*|FLAG\s+)([A-Z][A-Z\s]+?)(?:\n|CLASS|BUILT|LOA|$)', text, re.IGNORECASE)
    if m:
        return _clean(m.group(1))[:50]
    return None


def _extract_built(text: str) -> str | None:
    m = re.search(r'(?:BUILT|BLT)\s*:?\s*(\d{4})', text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _extract_class(text: str) -> str | None:
    m = re.search(r'(?:CLASS(?:IFICATION)?\s*:?\s*|CLASSED\s+)([A-Z]+(?:\s+[A-Z]+)?)', text, re.IGNORECASE)
    if m:
        val = _clean(m.group(1))[:50]
        if val.lower() not in ('class', 'highest'):
            return val
    # Common class notations inline
    m = re.search(r'\b(LR|ABS|NK|BV|DNV|GL|CCS|KR|RINA|PRS)\b', text)
    if m:
        return m.group(1)
    return None


def _extract_loa(text: str) -> str | None:
    m = re.search(r'LOA\s*[:/]?\s*([\d.]+)\s*M', text, re.IGNORECASE)
    if m:
        return m.group(1) + 'M'
    return None


def _extract_beam(text: str) -> str | None:
    m = re.search(r'(?:BEAM|BREADTH)\s*[:/]?\s*([\d.]+)\s*M', text, re.IGNORECASE)
    if m:
        return m.group(1) + 'M'
    return None


def _extract_vessel_type(text: str) -> str:
    t = text.upper()
    if 'SDBC' in t:
        return 'SDBC'
    if 'SDSTBC' in t:
        return 'SDSTBC'
    if 'BULK CARRIER' in t:
        return 'BULK CARRIER'
    if 'CAPESIZE' in t:
        return 'CAPESIZE BULK'
    if 'PANAMAX' in t:
        return 'PANAMAX BULK'
    if 'SUPRAMAX' in t or 'ULTRAMAX' in t:
        return 'SUPRAMAX BULK'
    if 'HANDYMAX' in t:
        return 'HANDYMAX BULK'
    if 'HANDYSIZE' in t:
        return 'HANDYSIZE BULK'
    return 'BULK CARRIER'


def _enrich(vessel: dict, section: str):
    """Try to fill in blank fields from a vessel detail section."""
    sec_up = section.upper()
    name = vessel.get('vessel_name', '')
    if name and name.upper() not in sec_up:
        return  # This section is not about this vessel

    if not vessel.get('flag'):
        vessel['flag'] = _extract_flag(section)
    if not vessel.get('built_year'):
        vessel['built_year'] = _extract_built(section)
    if not vessel.get('class_society'):
        vessel['class_society'] = _extract_class(section)
    if not vessel.get('loa'):
        vessel['loa'] = _extract_loa(section)
    if not vessel.get('beam'):
        vessel['beam'] = _extract_beam(section)
    if not vessel.get('vessel_type') or vessel.get('vessel_type') == 'BULK CARRIER':
        vt = _extract_vessel_type(section)
        if vt != 'BULK CARRIER':
            vessel['vessel_type'] = vt
    # Try enriching DWT from detailed specs
    if not vessel.get('vessel_size'):
        m = re.search(r'DWT\s*([\d,\.]+)\s*MT|(\d[\d,\.]+)\s*(?:MT\s+)?DWT', section, re.IGNORECASE)
        if m:
            val = (m.group(1) or m.group(2)).replace(',', '').strip()
            vessel['vessel_size'] = val + ' DWT'


# ── Main extractor ────────────────────────────────────────────────────────────

def extract_tonnage(text: str, email_id: int) -> list[dict]:
    """Extract all vessels from a tonnage email. Returns list of vessel dicts."""
    vessels: list[dict] = []
    text_up = text.upper()

    # ── Pattern 1: "MV VESSEL DWT XXXXX OPEN PORT O/A DATE" ─────────────────
    p1 = re.compile(
        r'(?:MV|M/V)\s+([A-Z][A-Z0-9\s]{2,35}?)\s+'
        r'DWT\s+([\d,\.]+)\s+'
        r'OPEN\s+([A-Z][A-Z\s,./\-]{2,40}?)\s+'
        r'O/A\s+([A-Z0-9\s\-/]+)',
        re.IGNORECASE | re.MULTILINE,
    )
    for m in p1.finditer(text_up):
        vessel_name = _clean(m.group(1))
        dwt = m.group(2).replace(',', '').replace('.', '')
        open_port = _clean(m.group(3))
        open_date = _clean(m.group(4))
        if not any(v['vessel_name'] == vessel_name for v in vessels):
            vessels.append({
                'email_id': email_id,
                'vessel_name': vessel_name,
                'vessel_size': dwt + ' DWT',
                'open_port': open_port,
                'open_date': open_date,
                'vessel_type': 'BULK CARRIER',
                'account_name': _extract_account(text),
                'flag': None, 'built_year': None, 'class_society': None,
                'loa': None, 'beam': None,
            })

    # ── Pattern 2: "VESSEL_NAME (XXK – SCRUBBER / YEAR) – OPEN PORT DATE" ───
    p2 = re.compile(
        r'([A-Z][A-Z\s]{3,30}?)\s*\((\d+)K\s*[-–][^)]{0,60}\)\s*[-–]+\s*OPEN\s+'
        r'([A-Z][A-Z\s,]{2,40}?),\s*([A-Z][A-Z\s]+?)\s+(\d{2}[-–]\d{2}\s+\w+|\d{1,2}\s+\w+)',
        re.IGNORECASE,
    )
    for m in p2.finditer(text_up):
        vessel_name = _clean(m.group(1))
        dwt_k = m.group(2)
        open_port = _clean(m.group(3)) + ', ' + _clean(m.group(4))
        open_date = _clean(m.group(5))
        if not any(v['vessel_name'] == vessel_name for v in vessels):
            vessels.append({
                'email_id': email_id,
                'vessel_name': vessel_name,
                'vessel_size': dwt_k + 'K DWT',
                'open_port': open_port,
                'open_date': open_date,
                'vessel_type': 'BULK CARRIER',
                'account_name': _extract_account(text),
                'flag': None, 'built_year': None, 'class_society': None,
                'loa': None, 'beam': None,
            })

    # ── Pattern 3: Single vessel intro "MV TRUE FRIEND/51K/ 09 - BEJAIA, 1ST JUNE" ─
    p3 = re.compile(
        r'(?:MV|M/V)\s+([A-Z][A-Z\s]{2,30}?)\s*/\s*(\d+)K\s*/\s*(\d{2})\s*[-–]\s*'
        r'([A-Z][A-Z\s,]+?),?\s*([0-9A-Z\s]+(?:JUNE|JULY|AUG|SEP|OCT|NOV|DEC|JAN|FEB|MAR|APR|MAY)[^\n]*)',
        re.IGNORECASE,
    )
    for m in p3.finditer(text_up):
        vessel_name = _clean(m.group(1))
        dwt_k = m.group(2)
        open_port = _clean(m.group(4))
        open_date = _clean(m.group(5))
        if not any(v['vessel_name'] == vessel_name for v in vessels):
            vessels.append({
                'email_id': email_id,
                'vessel_name': vessel_name,
                'vessel_size': dwt_k + 'K DWT',
                'open_port': open_port,
                'open_date': open_date,
                'vessel_type': 'BULK CARRIER',
                'account_name': _extract_account(text),
                'flag': None, 'built_year': None, 'class_society': None,
                'loa': None, 'beam': None,
            })

    # ── Enrich vessels from detail sections (separated by ---) ───────────────
    sections = re.split(r'\n[-]{10,}\n', text)
    for section in sections:
        for vessel in vessels:
            _enrich(vessel, section)

    # ── Fallback: single vessel email ────────────────────────────────────────
    if not vessels:
        v = _extract_single_vessel_fallback(text, email_id)
        if v:
            vessels.append(v)

    return vessels


def _extract_single_vessel_fallback(text: str, email_id: int) -> dict | None:
    text_up = text.upper()
    # Try "M/V: VESSEL_NAME" or "MV VESSEL_NAME\n"
    m = re.search(r'(?:M/V\s*:\s*|^MV\s+)([A-Z][A-Z0-9\s]{2,30})$', text_up, re.MULTILINE)
    if not m:
        m = re.search(r'(?:VESSEL|VSL)\s*[:\s]+([A-Z][A-Z0-9\s]{3,30})$', text_up, re.MULTILINE)
    if not m:
        return None

    vessel_name = _clean(m.group(1))
    dwt_m = re.search(r'DWT\s*([\d,\.]+)\s*MT|([\d,\.]+)\s*(?:MT\s+)?DWT', text_up)
    dwt = None
    if dwt_m:
        dwt = (dwt_m.group(1) or dwt_m.group(2)).replace(',', '') + ' DWT'

    open_port, open_date = _extract_open_port_date(text_up)

    return {
        'email_id': email_id,
        'vessel_name': vessel_name,
        'vessel_size': dwt,
        'open_port': open_port,
        'open_date': open_date,
        'vessel_type': _extract_vessel_type(text),
        'account_name': _extract_account(text),
        'flag': _extract_flag(text),
        'built_year': _extract_built(text),
        'class_society': _extract_class(text),
        'loa': _extract_loa(text),
        'beam': _extract_beam(text),
    }


def _extract_open_port_date(text_up: str) -> tuple[str | None, str | None]:
    m = re.search(r'OPEN\s+([A-Z][A-Z\s,]{2,40}?)\s+(?:O/A|ETA)?\s*(\d[^\n]{3,25})', text_up)
    if m:
        return _clean(m.group(1)), _clean(m.group(2))
    m = re.search(r'OPEN\s+([A-Z][A-Z\s,]{2,40})', text_up)
    if m:
        return _clean(m.group(1)), None
    return None, None
