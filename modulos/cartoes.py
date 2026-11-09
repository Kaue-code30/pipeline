"""Consultas SQLite parametrizadas para o banco de demonstração."""
import sqlite3
from contextlib import closing
from flask import request
import config


def conectar():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS cartoes '
                 '(numero TEXT, cpf_titular TEXT, fatura REAL)')
    conn.commit()
    return conn


def consultar_fatura(numero_cartao):
    with closing(conectar()) as conn:
        cursor = conn.execute('SELECT fatura FROM cartoes WHERE numero = ?', (numero_cartao,))
        return cursor.fetchone()


def buscar_cartoes_cliente():
    cpf = request.args.get('cpf')
    with closing(conectar()) as conn:
        return conn.execute('SELECT * FROM cartoes WHERE cpf_titular = ?', (cpf,)).fetchall()
