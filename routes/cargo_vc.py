import csv
import io
from flask import Blueprint, request, jsonify, Response
from database.db import get_session
from database.models import CargoVC

cargo_vc_bp = Blueprint('cargo_vc', __name__)


@cargo_vc_bp.route('/cargo_vc', methods=['GET'])
def get_cargo_vc():
    session = get_session()
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, int(request.args.get('per_page', 20)))
        search = request.args.get('search', '').strip()

        query = session.query(CargoVC)
        if search:
            query = query.filter(
                CargoVC.cargo_name.ilike(f'%{search}%') |
                CargoVC.loading_port.ilike(f'%{search}%') |
                CargoVC.discharge_port.ilike(f'%{search}%')
            )

        total = query.count()
        records = (
            query.order_by(CargoVC.id.desc())
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


@cargo_vc_bp.route('/cargo_vc/<int:record_id>', methods=['GET'])
def get_cargo_vc_record(record_id):
    session = get_session()
    try:
        obj = session.get(CargoVC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(obj.to_dict())
    finally:
        session.close()


@cargo_vc_bp.route('/cargo_vc/<int:record_id>', methods=['PATCH'])
def update_cargo_vc(record_id):
    session = get_session()
    try:
        obj = session.get(CargoVC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        data = request.get_json(force=True)
        allowed = [
            'account_name', 'cargo_name', 'loading_port', 'discharge_port',
            'laycan', 'cargo_type', 'quantity',
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


@cargo_vc_bp.route('/cargo_vc/<int:record_id>', methods=['DELETE'])
def delete_cargo_vc(record_id):
    session = get_session()
    try:
        obj = session.get(CargoVC, record_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        session.delete(obj)
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()


@cargo_vc_bp.route('/cargo_vc/export', methods=['GET'])
def export_cargo_vc_csv():
    session = get_session()
    try:
        records = session.query(CargoVC).order_by(CargoVC.id).all()
        output = io.StringIO()
        fields = ['id', 'email_id', 'account_name', 'cargo_name', 'loading_port',
                  'discharge_port', 'laycan', 'cargo_type', 'quantity']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())
        csv_bytes = output.getvalue().encode('utf-8')
        return Response(
            csv_bytes,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=cargo_vc_export.csv'},
        )
    finally:
        session.close()
