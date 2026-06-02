from flask import Blueprint, jsonify
from sqlalchemy import func
from database.db import get_session
from database.models import Email, Tonnage, CargoVC, CargoTC

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    session = get_session()
    try:
        total_emails    = session.query(func.count(Email.id)).scalar() or 0
        tonnage_count   = session.query(func.count(Tonnage.id)).scalar() or 0
        cargo_vc_count  = session.query(func.count(CargoVC.id)).scalar() or 0
        cargo_tc_count  = session.query(func.count(CargoTC.id)).scalar() or 0
        duplicate_count = session.query(func.count(Email.id)).filter(
            Email.is_duplicate == True  # noqa: E712
        ).scalar() or 0

        # Category breakdown
        by_category = (
            session.query(Email.category, func.count(Email.id))
            .group_by(Email.category)
            .all()
        )

        # Recent 5 emails
        recent = (
            session.query(Email)
            .order_by(Email.created_at.desc())
            .limit(5)
            .all()
        )

        return jsonify({
            'total_emails':    total_emails,
            'tonnage_records': tonnage_count,
            'cargo_vc_records': cargo_vc_count,
            'cargo_tc_records': cargo_tc_count,
            'duplicate_count': duplicate_count,
            'by_category': {cat: cnt for cat, cnt in by_category},
            'recent': [e.to_dict() for e in recent],
        })
    finally:
        session.close()


@stats_bp.route('/history', methods=['GET'])
def get_history():
    """Returns per-sender (broker) activity breakdown."""
    session = get_session()
    try:
        rows = (
            session.query(
                Email.sender,
                func.count(Email.id).label('total'),
                func.max(Email.created_at).label('last_seen'),
            )
            .group_by(Email.sender)
            .order_by(func.count(Email.id).desc())
            .all()
        )

        # Per-sender category breakdown
        cat_rows = (
            session.query(Email.sender, Email.category, func.count(Email.id))
            .group_by(Email.sender, Email.category)
            .all()
        )
        cat_map: dict = {}
        for sender, cat, cnt in cat_rows:
            cat_map.setdefault(sender, {})[cat] = cnt

        history = []
        for sender, total, last_seen in rows:
            history.append({
                'sender': sender,
                'total': total,
                'last_seen': last_seen.isoformat() if last_seen else None,
                'categories': cat_map.get(sender, {}),
            })

        return jsonify({'history': history})
    finally:
        session.close()


@stats_bp.route('/analytics', methods=['GET'])
def get_analytics():
    import re
    from datetime import datetime, timedelta, timezone
    from routes.matching import _parse_dwt

    session = get_session()
    try:
        # Total counts (KPIs)
        total_emails    = session.query(func.count(Email.id)).scalar() or 0
        tonnage_count   = session.query(func.count(Tonnage.id)).scalar() or 0
        cargo_vc_count  = session.query(func.count(CargoVC.id)).scalar() or 0
        cargo_tc_count  = session.query(func.count(CargoTC.id)).scalar() or 0

        # --- 1. Daily Volume Trend (Last 30 Days) ---
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=29)).date()

        trend_rows = (
            session.query(
                func.date(Email.created_at).label('date'),
                Email.category,
                func.count(Email.id).label('count')
            )
            .filter(func.date(Email.created_at) >= start_date)
            .group_by(func.date(Email.created_at), Email.category)
            .all()
        )

        # Pre-populate map with YYYY-MM-DD dates and 0 counts
        trend_map = {}
        for i in range(30):
            d = (start_date + timedelta(days=i)).isoformat()
            trend_map[d] = {'tonnage': 0, 'cargo_vc': 0, 'cargo_tc': 0}

        for d_val, cat, count in trend_rows:
            d_str = str(d_val) if d_val else ""
            if d_str in trend_map and cat in trend_map[d_str]:
                trend_map[d_str][cat] = count

        trend_labels = sorted(trend_map.keys())
        trend_series = {
            'tonnage': [trend_map[d]['tonnage'] for d in trend_labels],
            'cargo_vc': [trend_map[d]['cargo_vc'] for d in trend_labels],
            'cargo_tc': [trend_map[d]['cargo_tc'] for d in trend_labels],
        }

        # --- 2. Top Ports Activity ---
        # Voyage Charter
        vc_ports = session.query(CargoVC.loading_port, CargoVC.discharge_port).all()
        # Time Charter
        tc_ports = session.query(CargoTC.delivery_port, CargoTC.redelivery_port).all()

        port_counts = {}
        def _add_port(port_name):
            if port_name:
                p = port_name.upper().strip()
                if p and p not in ['—', 'UNKNOWN', 'N/A', 'NULL']:
                    # Remove common qualifiers like "PORT" or "EC" / "WC" for clean display
                    clean_p = re.sub(r'\bPORT\b', '', p).strip()
                    if clean_p:
                        port_counts[clean_p] = port_counts.get(clean_p, 0) + 1

        for lp, dp in vc_ports:
            _add_port(lp)
            _add_port(dp)
        for dp, rdp in tc_ports:
            _add_port(dp)
            _add_port(rdp)

        top_ports = sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # --- 3. Vessel Size Distribution ---
        vessels = session.query(Tonnage.vessel_size).all()

        size_buckets = {
            'Handysize/Handymax (< 40k)': 0,
            'Supramax/Ultramax (40-65k)': 0,
            'Panamax/Kamsarmax (65-85k)': 0,
            'Capesize (> 85k)': 0,
            'Unknown': 0
        }

        for (v_size_str,) in vessels:
            dwt = _parse_dwt(v_size_str)
            if dwt is None:
                size_buckets['Unknown'] += 1
            elif dwt < 40000:
                size_buckets['Handysize/Handymax (< 40k)'] += 1
            elif dwt <= 65000:
                size_buckets['Supramax/Ultramax (40-65k)'] += 1
            elif dwt <= 85000:
                size_buckets['Panamax/Kamsarmax (65-85k)'] += 1
            else:
                size_buckets['Capesize (> 85k)'] += 1

        return jsonify({
            'total_emails': total_emails,
            'tonnage_records': tonnage_count,
            'cargo_vc_records': cargo_vc_count,
            'cargo_tc_records': cargo_tc_count,
            'trend': {
                'labels': trend_labels,
                'series': trend_series
            },
            'top_ports': {
                'labels': [p[0] for p in top_ports],
                'data': [p[1] for p in top_ports]
            },
            'vessel_sizes': {
                'labels': list(size_buckets.keys()),
                'data': list(size_buckets.values())
            }
        })
    finally:
        session.close()

