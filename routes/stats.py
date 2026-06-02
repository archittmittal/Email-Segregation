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
