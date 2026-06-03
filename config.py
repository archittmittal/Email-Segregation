import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if we are running in a Hugging Face Space with persistent storage mounted at /data
if os.path.exists('/data') and os.access('/data', os.W_OK):
    DATA_DIR = '/data'
    print(f"[ShipSeg] Using Hugging Face persistent storage volume at: {DATA_DIR}")
else:
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    print(f"[ShipSeg] Using local directory for storage: {DATA_DIR}")

os.makedirs(DATA_DIR, exist_ok=True)

raw_db_url = os.environ.get('DATABASE_URL')
if raw_db_url:
    # SQLAlchemy 1.4+ requires postgresql:// instead of legacy postgres://
    if raw_db_url.startswith("postgres://"):
        DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = raw_db_url
else:
    DATABASE_URL = f'sqlite:///{os.path.join(DATA_DIR, "emails.db")}'

