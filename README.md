# Simulador de Cartões — Esteira DevSecOps

Aplicação Flask para um exercício de pipeline sequencial com oito etapas:
Gitleaks, Semgrep, build/testes Python, Trivy SCA, Docker Buildx + GHCR,
Trivy da imagem, homologação com ZAP Baseline e produção com aprovação manual.
O resumo executa mesmo quando uma etapa falha.

As vulnerabilidades dos módulos originais foram corrigidas. Os manifests
`k8s/` continuam como material dos exercícios de Kubernetes e não são
implantados pela esteira. O ambiente desta entrega é temporário e isolado
no runner do GitHub; não há hospedagem pública ou produção permanente.

Veja [etapas, relatórios, baseline e aprovação de produção](docs/esteira.md).

## Executar localmente

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

Abra `http://127.0.0.1:5000/`. `/saude` retorna `{"status":"ok"}`.
Nenhum usuário possui senha padrão. Para habilitar login, configure
`ADMIN_PASSWORD_HASH` com um hash scrypt gerado por Werkzeug.

`SECRET_KEY`, `DATABASE_PATH`, `UPLOAD_FOLDER` e `WEBHOOK_URLS` podem ser
fornecidos por variáveis de ambiente. Sem allowlist, webhooks ficam desabilitados.
Não versione credenciais nem relatórios contendo valores de segredos.

## Estrutura

- `.github/workflows/esteira.yml`: workflow e quality gates.
- `app.py`, `config.py`, `modulos/`: aplicação e configurações externas.
- `tests/`: testes de inicialização e regressões de segurança.
- `regras-banco/`: regras SAST do Semgrep.
- `.gitleaks.toml`, `.gitleaksignore`: regras e baseline histórica por ocorrência.
- `.zap/rules.tsv`: política informativa do DAST.
- `Dockerfile`: imagem não-root com Gunicorn e health check.
- `scripts/deploy-lab.sh`: validação da produção temporária após aprovação.
- `k8s/`: manifests didáticos legados, fora do deploy deste workflow.
