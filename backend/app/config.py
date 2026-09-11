import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./careerlens.db')
EMBEDDING_BACKEND = os.getenv('EMBEDDING_BACKEND', 'minilm')
MODEL_NAME = os.getenv('MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
MODEL_REVISION = os.getenv('MODEL_REVISION', 'c9745ed1d9f207416be6d2e6f8de32d1f16199bf')
MAX_BYTES = 5 * 1024 * 1024
MAX_TEXT = 40000
