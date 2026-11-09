"""
Simulador de Cartões de Crédito — aplicação de exemplo para o
laboratório de SonarQube.

As vulnerabilidades originais do exercício foram corrigidas para a
esteira DevSecOps. O ambiente de execução continua sendo um laboratório.
"""

from flask import Flask, jsonify, request

import config
from modulos import autenticacao, cartoes, notificacoes, relatorios

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route('/')
def inicio():
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<title>Simulador de cartões</title><h1>Simulador de cartões</h1>'
            '<ul><li><a href="/saude">Saúde</a></li>'
            '<li><a href="/cartoes">Cartões</a></li>'
            '<li><a href="/fatura">Fatura</a></li>'
            '<li><a href="/relatorio?formato=csv">Relatório CSV</a></li>'
            '<li><a href="/diagnostico?cmd=saude">Diagnóstico</a></li></ul></html>')


@app.errorhandler(ValueError)
def entrada_invalida(error):
    return jsonify({'erro': str(error)}), 400


@app.errorhandler(FileNotFoundError)
def arquivo_inexistente(error):
    return jsonify({'erro': 'Arquivo não encontrado'}), 404


@app.after_request
def cabecalhos_seguranca(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route("/saude")
def saude():
    """Endpoint de health check, usado pelas probes do Kubernetes no
    laboratório de segurança em cluster. Não faz nenhuma checagem real
    de dependências — propositalmente simples."""
    return jsonify({"status": "ok"})


@app.route("/login", methods=["POST"])
def login():
    usuario = request.form.get("usuario")
    senha = request.form.get("senha")
    if autenticacao.validar_login(usuario, senha):
        token = autenticacao.gerar_token_sessao()
        return jsonify({"token": token})
    return jsonify({"erro": "credenciais invalidas"}), 401


@app.route("/fatura")
def fatura():
    numero = request.args.get("numero_cartao")
    resultado = cartoes.consultar_fatura(numero)
    return jsonify(resultado)


@app.route("/cartoes")
def listar_cartoes():
    return jsonify(cartoes.buscar_cartoes_cliente())


@app.route("/relatorio")
def relatorio():
    formato = request.args.get("formato", "pdf")
    return relatorios.gerar_relatorio_pdf(formato)


@app.route("/extrato")
def extrato():
    arquivo = request.args.get("arquivo")
    return relatorios.baixar_extrato(arquivo)


@app.route("/diagnostico")
def diagnostico():
    cmd = request.args.get("cmd")
    return relatorios.executar_diagnostico(cmd)


@app.route("/webhook", methods=["POST"])
def webhook():
    url = request.form.get("url")
    payload = request.form.get("payload")
    return notificacoes.enviar_webhook(url, payload)


@app.route("/preferencias")
def preferencias():
    dados = request.args.get("dados")
    return str(notificacoes.carregar_preferencias_notificacao(dados))


@app.route("/simular-limite")
def simular_limite():
    expressao = request.args.get("expressao")
    resultado = notificacoes.calcular_limite_credito(expressao)
    return jsonify({"limite_estimado": resultado})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
