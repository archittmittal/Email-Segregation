from __future__ import annotations
import re
from flask import Blueprint, request, jsonify
from database.db import get_session
from database.models import Tonnage, CargoVC, CargoTC

matching_bp = Blueprint('matching', __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _port_score(port_a: str | None, port_b: str | None) -> int:
    if not port_a or not port_b:
        return 0
    a, b = port_a.upper().strip(), port_b.upper().strip()
    if a == b:
        return 50
    # Match on first meaningful token (e.g. city name)
    tok_a = re.split(r'[\s,/]+', a)[0]
    tok_b = re.split(r'[\s,/]+', b)[0]
    if tok_a and tok_b and tok_a == tok_b:
        return 35
    # Match if either contains the other (partial)
    if tok_a in b or tok_b in a:
        return 20
    # Match on last token (country code)
    last_a = re.split(r'[\s,/]+', a)[-1]
    last_b = re.split(r'[\s,/]+', b)[-1]
    if last_a and last_b and last_a == last_b and len(last_a) >= 2:
        return 10
    return 0


def _parse_dwt(size_str: str | None) -> float | None:
    if not size_str:
        return None
    m = re.search(r'([\d,\.]+)', size_str.replace(',', ''))
    if m:
        try:
            val = float(m.group(1))
            # Handle "56K DWT" style
            if 'K' in (size_str or '').upper() and val < 1000:
                val *= 1000
            return val
        except ValueError:
            return None
    return None


def _parse_quantity(qty_str: str | None) -> float | None:
    if not qty_str:
        return None
    # Strip out percentages like "10PCT" or "10%"
    clean_str = re.sub(r'\b\d+\s*(?:PCT|%)\b', '', qty_str, flags=re.IGNORECASE)
    # Extract numbers
    nums = re.findall(r'\b\d+[\d,\.]*\b', clean_str)
    vals = []
    for n in nums:
        try:
            val = float(n.replace(',', ''))
            vals.append(val)
        except ValueError:
            pass
    if not vals:
        return None
    return sum(vals) / len(vals)


def _size_score(dwt_str: str | None, qty_str: str | None) -> int:
    dwt = _parse_dwt(dwt_str)
    qty = _parse_quantity(qty_str)
    if not dwt or not qty or qty == 0:
        return 0
    ratio = dwt / qty
    if 0.6 <= ratio <= 1.6:   # ±40% of cargo fills the vessel
        return 20
    if 0.4 <= ratio <= 2.0:
        return 10
    return 0


def _date_score(open_date: str | None, laycan: str | None) -> int:
    """
    Rough textual date overlap scoring. We extract first year + month mentioned
    in each string and compare proximity in months.
    """
    if not open_date or not laycan:
        return 0

    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'june': 6, 'jul': 7, 'july': 7, 'aug': 8, 'sep': 9, 'oct': 10,
        'nov': 11, 'dec': 12,
    }

    def _extract_month_year(s: str):
        s_lo = s.lower()
        m = re.search(r'\b(\d{1,2})\b', s)
        day = int(m.group(1)) if m else 1
        for token, num in month_map.items():
            if token in s_lo:
                from datetime import datetime
                current_year = datetime.now().year
                yr_m = re.search(r'\b(20\d{2})\b', s)
                yr = int(yr_m.group(1)) if yr_m else current_year
                return (yr, num, day)
        return None

    od = _extract_month_year(open_date)
    lc = _extract_month_year(laycan)
    if not od or not lc:
        return 0

    # Difference in months
    diff = abs((od[0] * 12 + od[1]) - (lc[0] * 12 + lc[1]))
    if diff == 0:
        return 30
    if diff == 1:
        return 20
    if diff == 2:
        return 10
    return 0


def _score_tonnage_vs_vc(t: Tonnage, c: CargoVC) -> int:
    port  = _port_score(t.open_port, c.loading_port)
    date  = _date_score(t.open_date, c.laycan)
    size  = _size_score(t.vessel_size, c.quantity)
    return min(100, port + date + size)


def _score_tonnage_vs_tc(t: Tonnage, c: CargoTC) -> int:
    port  = _port_score(t.open_port, c.delivery_port)
    date  = _date_score(t.open_date, c.laycan)
    size  = _size_score(t.vessel_size, None)  # TC rarely specifies exact quantity
    return min(100, port + date + size + 10)   # +10 base for TC (size less critical)


# ── Routes ────────────────────────────────────────────────────────────────────

@matching_bp.route('/matches', methods=['GET'])
def get_matches():
    """
    GET /api/matches?mode=tonnage_to_vc&id=<tonnage_id>
    GET /api/matches?mode=tonnage_to_tc&id=<tonnage_id>
    GET /api/matches?mode=vc_to_tonnage&id=<cargo_vc_id>
    GET /api/matches?mode=tc_to_tonnage&id=<cargo_tc_id>
    GET /api/matches?mode=all  → full cross-match summary (top-5 per vessel)
    """
    mode = request.args.get('mode', 'all')
    record_id = request.args.get('id', type=int)

    session = get_session()
    try:
        if mode == 'tonnage_to_vc':
            if not record_id:
                return jsonify({'error': 'id required'}), 400
            vessel = session.get(Tonnage, record_id)
            if not vessel:
                return jsonify({'error': 'Tonnage record not found'}), 404
            cargos = session.query(CargoVC).all()
            matches = sorted(
                [{'cargo_vc': c.to_dict(), 'score': _score_tonnage_vs_vc(vessel, c)} for c in cargos],
                key=lambda x: x['score'], reverse=True,
            )
            return jsonify({'vessel': vessel.to_dict(), 'matches': matches, 'mode': mode})

        elif mode == 'tonnage_to_tc':
            if not record_id:
                return jsonify({'error': 'id required'}), 400
            vessel = session.get(Tonnage, record_id)
            if not vessel:
                return jsonify({'error': 'Tonnage record not found'}), 404
            cargos = session.query(CargoTC).all()
            matches = sorted(
                [{'cargo_tc': c.to_dict(), 'score': _score_tonnage_vs_tc(vessel, c)} for c in cargos],
                key=lambda x: x['score'], reverse=True,
            )
            return jsonify({'vessel': vessel.to_dict(), 'matches': matches, 'mode': mode})

        elif mode == 'vc_to_tonnage':
            if not record_id:
                return jsonify({'error': 'id required'}), 400
            cargo = session.get(CargoVC, record_id)
            if not cargo:
                return jsonify({'error': 'Cargo VC record not found'}), 404
            vessels = session.query(Tonnage).all()
            matches = sorted(
                [{'vessel': v.to_dict(), 'score': _score_tonnage_vs_vc(v, cargo)} for v in vessels],
                key=lambda x: x['score'], reverse=True,
            )
            return jsonify({'cargo_vc': cargo.to_dict(), 'matches': matches, 'mode': mode})

        elif mode == 'tc_to_tonnage':
            if not record_id:
                return jsonify({'error': 'id required'}), 400
            cargo = session.get(CargoTC, record_id)
            if not cargo:
                return jsonify({'error': 'Cargo TC record not found'}), 404
            vessels = session.query(Tonnage).all()
            matches = sorted(
                [{'vessel': v.to_dict(), 'score': _score_tonnage_vs_tc(v, cargo)} for v in vessels],
                key=lambda x: x['score'], reverse=True,
            )
            return jsonify({'cargo_tc': cargo.to_dict(), 'matches': matches, 'mode': mode})

        else:  # mode == 'all' — top-5 VC matches per vessel
            vessels = session.query(Tonnage).all()
            vc_cargos = session.query(CargoVC).all()
            tc_cargos = session.query(CargoTC).all()
            summary = []
            for v in vessels:
                vc_matches = sorted(
                    [{'id': c.id, 'cargo_name': c.cargo_name, 'loading_port': c.loading_port,
                      'laycan': c.laycan, 'score': _score_tonnage_vs_vc(v, c)} for c in vc_cargos],
                    key=lambda x: x['score'], reverse=True,
                )[:3]
                tc_matches = sorted(
                    [{'id': c.id, 'cargo_name': c.cargo_name, 'delivery_port': c.delivery_port,
                      'laycan': c.laycan, 'score': _score_tonnage_vs_tc(v, c)} for c in tc_cargos],
                    key=lambda x: x['score'], reverse=True,
                )[:3]
                summary.append({
                    'vessel': {
                        'id': v.id,
                        'vessel_name': v.vessel_name,
                        'open_port': v.open_port,
                        'open_date': v.open_date,
                        'vessel_size': v.vessel_size,
                    },
                    'top_vc': vc_matches,
                    'top_tc': tc_matches,
                    'best_score': max(
                        (m['score'] for m in vc_matches + tc_matches), default=0
                    ),
                })
            summary.sort(key=lambda x: x['best_score'], reverse=True)
            return jsonify({'summary': summary, 'mode': 'all'})

    finally:
        session.close()
