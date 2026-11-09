"""Relatórios e diagnóstico sem interpretação de comandos externos."""
import platform
import sys
from pathlib import Path
from flask import Response
import config


def gerar_relatorio_pdf(formato):
    if formato == 'csv':
        return Response('descricao,valor\nLimite demonstrativo,0\n', mimetype='text/csv')
    if formato != 'pdf':
        raise ValueError('Formato deve ser pdf ou csv')
    stream = b'BT /F1 16 Tf 50 750 Td (Relatorio demonstrativo de cartoes) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
               b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    content = bytearray(b'%PDF-1.4\n')
    offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(str(number).encode() + b' 0 obj\n' + obj + b'\nendobj\n')
    xref = len(content)
    content.extend(b'xref\n0 6\n0000000000 65535 f \n')
    for offset in offsets:
        content.extend(f'{offset:010d} 00000 n \n'.encode())
    content.extend(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return Response(bytes(content), mimetype='application/pdf')


def baixar_extrato(nome_arquivo):
    if not isinstance(nome_arquivo, str) or not nome_arquivo:
        raise ValueError('Informe o arquivo do extrato')
    root = Path(config.UPLOAD_FOLDER).resolve()
    path = (root / nome_arquivo).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Caminho de extrato não autorizado')
    return path.read_text(encoding='utf-8')


def executar_diagnostico(comando_usuario):
    diagnostics = {'saude': 'ok', 'python': sys.version.split()[0], 'sistema': platform.system()}
    if comando_usuario not in diagnostics:
        raise ValueError('Diagnóstico deve ser saude, python ou sistema')
    return diagnostics[comando_usuario]
