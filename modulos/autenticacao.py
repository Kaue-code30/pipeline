"""Autenticação com hash scrypt e tokens criptográficos."""
import os
import secrets
from werkzeug.security import check_password_hash, generate_password_hash

USUARIOS = {}
if os.getenv('ADMIN_PASSWORD_HASH'):
    USUARIOS['admin'] = os.environ['ADMIN_PASSWORD_HASH']


def gerar_hash_senha(senha):
    return generate_password_hash(senha, method='scrypt')


def validar_login(usuario, senha):
    if not isinstance(usuario, str) or not isinstance(senha, str):
        return False
    stored_hash = USUARIOS.get(usuario)
    return bool(stored_hash and check_password_hash(stored_hash, senha))


def gerar_token_sessao():
    return secrets.token_urlsafe(32)
