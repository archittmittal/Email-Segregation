import csv
import io
from flask import Blueprint, request, jsonify, Response
from database.db import get_session
from database.models import CargoTC

cargo_tc_bp = Blueprint('cargo_tc', __name__)


@cargo_tc_bp.route('/cargo_tc', methods=['GET'])
def get_cargo_tc():
    session = get_session()
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, int(request.args.get('per_page', 20)))
        search = request.args.get('search', '').strip()

        query = session.query(CargoTC)
        if search:
            query = query.filter(
                CargoTC.cargo_name.ilike(f'%{search}%') |
                CargoTC.delivery_port.ilike(f'%{search}%') |
                CargoTC.redelivery_port.ilike(f'%{search}%')
            )

        total = query.count()
        records = (
            query.order_by(CargoTC.id.desc())
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


@cargo_tc_bp.route('/cargo_tc/<int:record_id>', methods=['GET'])
def get_cargo_tc_record(record_id):
    session = get_session()
    try:
        obj = session.get(CargoTC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(obj.to_dict())
    finally:
        session.close()


@cargo_tc_bp.route('/cargo_tc/<int:record_id>', methods=['PATCH'])
def update_cargo_tc(record_id):
    session = get_session()
    try:
        obj = session.get(CargoTC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        data = request.get_json(force=True)
        allowed = [
            'account_name', 'cargo_name', 'delivery_port', 'redelivery_port',
            'duration', 'laycan', 'cargo_type',
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


@cargo_tc_bp.route('/cargo_tc/<int:record_id>', methods=['DELETE'])
def delete_cargo_tc(record_id):
    session = get_session()
    try:
        obj = session.get(CargoTC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        session.delete(obj)
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()


@cargo_tc_bp.route('/cargo_tc/export', methods=['GET'])
def export_cargo_tc_csv():
    session = get_session()
    try:
        records = session.query(CargoTC).order_by(CargoTC.id).all()
        output = io.StringIO()
        fields = ['id', 'email_id', 'account_name', 'cargo_name', 'delivery_port',
                  'redelivery_port', 'duration', 'laycan', 'cargo_type']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())
        csv_bytes = output.getvalue().encode('utf-8')
        return Response(
            csv_bytes,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=cargo_tc_export.csv'},
        )
    finally:
        session.close()
