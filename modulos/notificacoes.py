"""JSON, aritmética limitada e webhooks em destinos configurados."""
import ast
import json
import math
import operator
from urllib.parse import urlsplit
import requests
import config


def enviar_webhook(url_destino, payload):
    if url_destino not in config.WEBHOOK_URLS:
        raise ValueError('Destino de webhook não autorizado')
    parsed = urlsplit(url_destino)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Webhook deve usar HTTPS sem credenciais na URL')
    response = requests.post(url_destino, json={'payload': payload},
                             timeout=5, allow_redirects=False)
    if 300 <= response.status_code < 400:
        raise ValueError('Redirecionamento de webhook não permitido')
    response.raise_for_status()
    return response.text


def carregar_preferencias_notificacao(dados_serializados):
    if not isinstance(dados_serializados, str) or len(dados_serializados) > 4096:
        raise ValueError('Preferências devem ser um objeto JSON de até 4096 caracteres')
    dados = json.loads(dados_serializados)
    if not isinstance(dados, dict):
        raise ValueError('Preferências devem ser um objeto JSON')
    return dados


def calcular_limite_credito(expressao):
    if not isinstance(expressao, str) or not expressao or len(expressao) > 128:
        raise ValueError('Expressão inválida')
    try:
        tree = ast.parse(expressao, mode='eval')
    except SyntaxError as exc:
        raise ValueError('Expressão inválida') from exc
    if sum(1 for _ in ast.walk(tree)) > 32:
        raise ValueError('Expressão muito complexa')
    operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                  ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod}

    def calculate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            try:
                value = operations[type(node.op)](calculate(node.left), calculate(node.right))
            except (ZeroDivisionError, OverflowError) as exc:
                raise ValueError('Operação aritmética inválida') from exc
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = calculate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError('Somente operações aritméticas são permitidas')
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError('Resultado fora do limite')
        return value

    return calculate(tree.body)
