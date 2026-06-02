import csv
import io
from flask import Blueprint, request, jsonify, Response
from database.db import get_session
from database.models import Tonnage

tonnage_bp = Blueprint('tonnage', __name__)


@tonnage_bp.route('/tonnage', methods=['GET'])
def get_tonnage():
    session = get_session()
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(1000, int(request.args.get('per_page', 20)))
        search = request.args.get('search', '').strip()
        port = request.args.get('port', '').strip()

        query = session.query(Tonnage)
        if search:
            query = query.filter(
                Tonnage.vessel_name.ilike(f'%{search}%') |
                Tonnage.open_port.ilike(f'%{search}%')
            )
        if port:
            query = query.filter(Tonnage.open_port.ilike(f'%{port}%'))

        total = query.count()
        records = (
            query.order_by(Tonnage.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            'records': [r.to_dict() for r in records],
            'total': total,
            'page': page,
            'per_page': per_page,
        })
    finally:
        session.close()


@tonnage_bp.route('/tonnage/<int:record_id>', methods=['GET'])
def get_tonnage_record(record_id):
    session = get_session()
    try:
        obj = session.get(Tonnage, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(obj.to_dict())
    finally:
        session.close()


@tonnage_bp.route('/tonnage/<int:record_id>', methods=['PATCH'])
def update_tonnage(record_id):
    session = get_session()
    try:
        obj = session.get(Tonnage, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        data = request.get_json(force=True)
        allowed = [
            'vessel_name', 'account_name', 'open_port', 'open_date',
            'vessel_type', 'vessel_size', 'flag', 'built_year', 'class_society',
            'loa', 'beam',
        ]
        for field in allowed:
            if field in data:
                setattr(obj, field, data[field])
        session.commit()
        return jsonify(obj.to_dict())
    except Exception as exc:
        session.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        session.close()


@tonnage_bp.route('/tonnage/<int:record_id>', methods=['DELETE'])
def delete_tonnage(record_id):
    session = get_session()
    try:
        obj = session.get(Tonnage, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        session.delete(obj)
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()


@tonnage_bp.route('/tonnage/export', methods=['GET'])
def export_tonnage_csv():
    session = get_session()
    try:
        records = session.query(Tonnage).order_by(Tonnage.id).all()
        output = io.StringIO()
        fields = ['id', 'email_id', 'vessel_name', 'account_name', 'open_port',
                  'open_date', 'vessel_type', 'vessel_size', 'flag', 'built_year',
                  'class_society', 'loa', 'beam']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())
        csv_bytes = output.getvalue().encode('utf-8')
        return Response(
            csv_bytes,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=tonnage_export.csv'},
        )
    finally:
        session.close()
