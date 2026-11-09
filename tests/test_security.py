"""Regressões de segurança dos pontos encontrados pelos scanners."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from modulos import autenticacao, cartoes, notificacoes, relatorios


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_hash_scrypt_e_autenticacao(self):
        hash_value = autenticacao.gerar_hash_senha('senha-temporaria-de-teste')
        self.assertTrue(hash_value.startswith('scrypt:'))
        with patch.dict(autenticacao.USUARIOS, {'teste': hash_value}, clear=True):
            self.assertTrue(autenticacao.validar_login('teste', 'senha-temporaria-de-teste'))
            self.assertFalse(autenticacao.validar_login('teste', 'incorreta'))
            self.assertFalse(autenticacao.validar_login('teste', None))

    def test_calculo_sem_execucao_de_codigo(self):
        self.assertEqual(notificacoes.calcular_limite_credito('(100 + 50) * 2'), 300)
        for expression in ['__import__("os").getcwd()', '2 ** 1000000', '1/0', '1e309', 'True']:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                notificacoes.calcular_limite_credito(expression)

    def test_preferencias_json(self):
        self.assertEqual(notificacoes.carregar_preferencias_notificacao('{"email":true}'), {'email': True})
        for payload in ['[]', '800495', '{invalido}']:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                notificacoes.carregar_preferencias_notificacao(payload)

    def test_webhook_bloqueia_destino_nao_autorizado(self):
        with patch('modulos.notificacoes.requests.post') as post:
            self.assertEqual(self.client.post('/webhook', data={'url': 'http://127.0.0.1/'}).status_code, 400)
            post.assert_not_called()

    def test_webhook_sem_redirecionamento(self):
        with patch('config.WEBHOOK_URLS', ('https://example.com/hook',)), \
                patch('modulos.notificacoes.requests.post') as post:
            post.return_value.status_code = 302
            with self.assertRaises(ValueError):
                notificacoes.enviar_webhook('https://example.com/hook', 'teste')
            self.assertFalse(post.call_args.kwargs['allow_redirects'])

    def test_extrato_bloqueia_traversal(self):
        with tempfile.TemporaryDirectory() as folder, patch('config.UPLOAD_FOLDER', folder):
            Path(folder, 'extrato.txt').write_text('extrato', encoding='utf-8')
            self.assertEqual(relatorios.baixar_extrato('extrato.txt'), 'extrato')
            with self.assertRaises(ValueError):
                relatorios.baixar_extrato('../config.py')

    def test_diagnostico_nao_executa_shell(self):
        self.assertEqual(self.client.get('/diagnostico?cmd=saude').text, 'ok')
        self.assertEqual(self.client.get('/diagnostico?cmd=saude;id').status_code, 400)

    def test_sql_parametrizado(self):
        with tempfile.TemporaryDirectory() as folder, patch('config.DATABASE_PATH', str(Path(folder, 'test.db'))):
            conn = cartoes.conectar()
            conn.execute('INSERT INTO cartoes VALUES (?, ?, ?)', ('123', '456', 100))
            conn.commit()
            conn.close()
            self.assertEqual(cartoes.consultar_fatura('123'), (100.0,))
            self.assertIsNone(cartoes.consultar_fatura("' OR 1=1 --"))
            self.assertEqual(self.client.get('/cartoes', query_string={'cpf': "' OR 1=1 --"}).json, [])

    def test_relatorio_valida_formato(self):
        self.assertTrue(self.client.get('/relatorio').data.startswith(b'%PDF-1.4'))
        self.assertEqual(self.client.get('/relatorio?formato=csv').mimetype, 'text/csv')
        self.assertEqual(self.client.get('/relatorio?formato=pdf;id').status_code, 400)

    def test_login_sem_dados(self):
        self.assertEqual(self.client.post('/login').status_code, 401)

    def test_pagina_inicial_para_spider(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/saude"', response.data)
