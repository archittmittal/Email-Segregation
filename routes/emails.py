import hashlib
import io
import re
import logging

from flask import Blueprint, request, jsonify
from database.db import get_session
from database.models import Email
from classification.classifier import classify
from extraction.extractor import extract
from ingestion.email_parser import parse_email, parse_eml_bytes, extract_text_from_attachment

logger = logging.getLogger(__name__)
emails_bp = Blueprint('emails', __name__)


# ── Fingerprint helper ────────────────────────────────────────────────────────

def _fingerprint(text: str) -> str:
    """Normalise and hash first 1000 chars for dedup detection."""
    normalised = re.sub(r'[\s\W]+', '', text.lower())[:1000]
    return hashlib.sha256(normalised.encode()).hexdigest()


# ── Helper: classify + extract + save ─────────────────────────────────────────

def _process_and_save(raw_text: str, subject: str, sender: str, session) -> dict:
    """Run classify→extract→save pipeline. Returns result dict."""
    fp = _fingerprint(raw_text)

    # Dedup check
    existing = session.query(Email).filter_by(fingerprint=fp).first()
    is_dup = existing is not None
    duplicated_of = existing.id if existing else None

    category, confidence = classify(raw_text)

    email_obj = Email(
        subject=subject,
        sender=sender,
        raw_body=raw_text,
        category=category,
        confidence=confidence,
        is_duplicate=is_dup,
        fingerprint=fp,
    )
    session.add(email_obj)
    session.flush()

    extracted = extract(category, raw_text, email_obj.id, session)
    session.commit()

    result = {
        'email': email_obj.to_dict(),
        'extracted': extracted,
        'category': category,
        'confidence': round(confidence, 3),
        'is_duplicate': is_dup,
    }
    if duplicated_of:
        result['duplicated_of'] = duplicated_of
    return result


# ── GET /api/emails ───────────────────────────────────────────────────────────

@emails_bp.route('/emails', methods=['GET'])
def get_emails():
    session = get_session()
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, int(request.args.get('per_page', 20)))
        category = request.args.get('category', '').strip() or None
        search = request.args.get('search', '').strip()
        show_dupes = request.args.get('duplicates_only', '').lower() == 'true'

        query = session.query(Email)
        if category:
            query = query.filter(Email.category == category)
        if search:
            query = query.filter(
                Email.raw_body.ilike(f'%{search}%') |
                Email.subject.ilike(f'%{search}%')
            )
        if show_dupes:
            query = query.filter(Email.is_duplicate == True)  # noqa: E712

        total = query.count()
        emails = (
            query.order_by(Email.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            'emails': [e.to_dict() for e in emails],
            'total': total,
            'page': page,
            'per_page': per_page,
        })
    finally:
        session.close()


# ── POST /api/emails (paste / text submit) ────────────────────────────────────

@emails_bp.route('/emails', methods=['POST'])
def process_email():
    data = request.get_json(force=True)
    raw_text = (data.get('text') or '').strip()
    subject  = (data.get('subject') or 'Manual Input').strip()
    sender   = (data.get('sender') or 'manual@system').strip()

    if not raw_text:
        return jsonify({'error': 'No email text provided'}), 400

    session = get_session()
    try:
        result = _process_and_save(raw_text, subject, sender, session)
        status = 200 if result['is_duplicate'] else 201
        return jsonify(result), status
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to process email paste input")
        return jsonify({'error': 'An internal error occurred while processing the email.'}), 500
    finally:
        session.close()


# ── POST /api/emails/upload (file upload: .eml / .txt / .pdf) ────────────────

@emails_bp.route('/emails/upload', methods=['POST'])
def upload_email():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    f = request.files['file']
    filename = (f.filename or '').lower()
    raw_bytes = f.read()

    subject = request.form.get('subject', '').strip()
    sender  = request.form.get('sender', '').strip()

    try:
        if filename.endswith('.eml'):
            parsed = parse_eml_bytes(raw_bytes)
            raw_text = parsed['body']
            subject  = subject or parsed.get('subject', 'Uploaded .eml')
            sender   = sender  or parsed.get('sender', 'unknown@upload')
        elif filename.endswith('.txt'):
            raw_text = raw_bytes.decode('utf-8', errors='replace')
            parsed   = parse_email(raw_text)
            subject  = subject or parsed.get('subject', 'Uploaded .txt')
            sender   = sender  or parsed.get('sender', 'unknown@upload')
            raw_text = parsed.get('body', raw_text)
        elif filename.endswith('.pdf'):
            raw_text = extract_text_from_attachment('file.pdf', raw_bytes)
            subject  = subject or 'Uploaded PDF'
            sender   = sender  or 'unknown@upload'
        else:
            return jsonify({'error': 'Unsupported file type. Use .eml, .txt, or .pdf'}), 400

        if not raw_text or not raw_text.strip():
            return jsonify({'error': 'Could not extract text from file'}), 422
    except Exception as exc:
        return jsonify({'error': f'File parse error: {str(exc)}'}), 422

    session = get_session()
    try:
        result = _process_and_save(raw_text.strip(), subject or 'Uploaded File', sender, session)
        status = 200 if result['is_duplicate'] else 201
        return jsonify(result), status
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to process email upload input")
        return jsonify({'error': 'An internal error occurred while processing the uploaded file.'}), 500
    finally:
        session.close()


# ── GET /api/emails/<id> ──────────────────────────────────────────────────────

@emails_bp.route('/emails/<int:email_id>', methods=['GET'])
def get_email(email_id):
    session = get_session()
    try:
        obj = session.get(Email, email_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(obj.to_dict(include_extracted=True))
    finally:
        session.close()


# ── DELETE /api/emails/<id> ───────────────────────────────────────────────────

@emails_bp.route('/emails/<int:email_id>', methods=['DELETE'])
def delete_email(email_id):
    session = get_session()
    try:
        obj = session.get(Email, email_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        session.delete(obj)
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()


# ── GET /api/emails/duplicates ────────────────────────────────────────────────

@emails_bp.route('/emails/duplicates', methods=['GET'])
def get_duplicates():
    session = get_session()
    try:
        dupes = (
            session.query(Email)
            .filter(Email.is_duplicate == True)  # noqa: E712
            .order_by(Email.created_at.desc())
            .all()
        )
        return jsonify({'duplicates': [e.to_dict() for e in dupes], 'total': len(dupes)})
    finally:
        session.close()
