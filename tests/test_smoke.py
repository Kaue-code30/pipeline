"""Verificações mínimas de inicialização usadas pelo build da esteira."""

import unittest

from app import app


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_saude(self):
        response = self.client.get('/saude')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_rota_inexistente(self):
        self.assertEqual(self.client.get('/rota-inexistente').status_code, 404)

    def test_login_invalido(self):
        response = self.client.post('/login', data={
            'usuario': 'usuario-inexistente', 'senha': 'senha-invalida',
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {'erro': 'credenciais invalidas'})


if __name__ == '__main__':
    unittest.main()
