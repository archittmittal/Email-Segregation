import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from database.db import init_db
from routes.emails import emails_bp
from routes.tonnage import tonnage_bp
from routes.cargo_vc import cargo_vc_bp
from routes.cargo_tc import cargo_tc_bp
from routes.stats import stats_bp
from routes.matching import matching_bp

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB file size limit

# Configure CORS dynamically based on allowed origins environment variable
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
if allowed_origins == '*':
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    CORS(app, resources={r"/api/*": {"origins": allowed_origins.split(',')}})

# ── API blueprints ─────────────────────────────────────────────────────────────
app.register_blueprint(emails_bp,   url_prefix='/api')
app.register_blueprint(tonnage_bp,  url_prefix='/api')
app.register_blueprint(cargo_vc_bp, url_prefix='/api')
app.register_blueprint(cargo_tc_bp, url_prefix='/api')
app.register_blueprint(stats_bp,    url_prefix='/api')
app.register_blueprint(matching_bp, url_prefix='/api')


# ── Frontend SPA ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def catch_all(path):
    # Serve static files; fall back to index.html for SPA routing
    full_path = os.path.join(app.static_folder, path)
    if os.path.isfile(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ── Startup ───────────────────────────────────────────────────────────────────
def startup():
    init_db()
    # Import classifier to trigger training at startup (fast, ~1 s)
    from classification.classifier import classify  # noqa: F401
    print("[ShipSeg] Database initialised. Classifier ready.")


startup()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
