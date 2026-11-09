"""Configurações externas do simulador."""
import os
import secrets
import tempfile
from pathlib import Path

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'cartoes_db')
DATABASE_PATH = os.getenv('DATABASE_PATH', str(Path(tempfile.gettempdir()) / 'cartoes.db'))
API_KEY_BANDEIRA = os.getenv('API_KEY_BANDEIRA')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(Path(tempfile.gettempdir()) / 'extratos'))
WEBHOOK_URLS = tuple(url.strip() for url in os.getenv('WEBHOOK_URLS', '').split(',') if url.strip())
