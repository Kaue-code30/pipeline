# Esteira DevSecOps

O workflow `.github/workflows/esteira.yml` executa no push para `main`,
em PRs destinados a `main` e manualmente pelo GitHub Actions.
As oito etapas são sequenciais, com bloqueio se a etapa anterior falhar.
O job **Resumo da Esteira** usa `if: always()` e publica o resultado mesmo
após falhas, respeitando a disponibilidade e o cancelamento do GitHub.

| Etapa | Ferramenta | Artifact | Gate |
| --- | --- | --- | --- |
| 1. Segredos | Gitleaks: histórico e estado atual | `relatorio-01-gitleaks` | Qualquer achado novo/atual ou erro bloqueia |
| 2. SAST | Semgrep com as regras locais | `relatorio-02-semgrep` | Qualquer achado ou erro bloqueia |
| 3. Build e testes | pip, compileall, unittest e tar | `relatorio-03-build` | Falhas de instalação, testes ou empacotamento bloqueiam |
| 4. SCA | Trivy fs | `relatorio-04-trivy-sca` | HIGH/CRITICAL bloqueiam |
| 5. Build e push | Docker Buildx e GHCR | `relatorio-05-docker-build` | Falha de build, exportação ou push bloqueia |
| 6. Imagem | Trivy image | `relatorio-06-trivy-image` | HIGH/CRITICAL bloqueiam |
| 7. Homologação e DAST | Docker e ZAP Baseline | `relatorio-07-homologacao-zap` | Achados informativos; erro operacional bloqueia |
| 8. Aprovação e produção | GitHub Environment e Docker | `relatorio-08-producao` | Aprovação manual e health check |

O artifact do resumo chama-se `resumo-da-esteira`. Etapas puladas não geram
relatórios. Cada job publica seus relatórios com `if: always()`.

## Segredos legados

O fork herdou ocorrências dos exercícios em seis commits. O relatório da
execução `42714024548` identificou 92 ocorrências: 78 em um antigo `leaks.json`,
13 nos exemplos anteriores e um falso positivo no rótulo do resumo.
Essas ocorrências foram registradas individualmente por fingerprint em
`.gitleaksignore`, como baseline legada documentada. Isso não exclui arquivos
inteiros, não ignora achados de novos commits e não reescreve o histórico.

Além da varredura Git, o job exporta o estado atual via `git archive` e
executa `gitleaks dir` **sem a baseline**. Assim, um valor antigo ainda presente
no código atual também bloqueia. Os relatórios mascaram os valores.
Credenciais reais anteriormente utilizadas precisam ser revogadas no serviço
de origem; a baseline não apaga nem revoga credenciais históricas.

## Correções da aplicação

- Scrypt substitui MD5; o hash do admin vem de `ADMIN_PASSWORD_HASH`.
- Tokens usam `secrets`, e o modo debug fica desativado.
- Preferências aceitam objetos JSON, sem desserialização de objetos Python.
- A calculadora interpreta apenas operações aritméticas limitadas via AST.
- Diagnósticos aceitam somente `saude`, `python` e `sistema`, sem shell.
- Extratos ficam restritos a `UPLOAD_FOLDER`, inclusive após resolver caminhos.
- Relatórios PDF/CSV são gerados sem executar comandos externos.
- Webhooks exigem URL HTTPS exata em `WEBHOOK_URLS` e não seguem redirects.
- Consultas SQLite usam parâmetros. A regra taint analisa o argumento SQL,
  sem tratar valores vinculados de uma consulta parametrizada como código SQL.

Os testes cobrem comportamento e regressões de injeção, caminhos, autenticação
e validação de entrada. A página `/` fornece links para o spider do ZAP.

## Dependências, imagem e GHCR

Python 3.12 instala as dependências num virtualenv limpo; `pip check`,
compilação e testes precisam passar. `pip freeze` registra as versões
efetivamente resolvidas, que são usadas tanto no SCA quanto no Docker build.
O pacote fonte é validado por SHA-256 antes do build da imagem.

A imagem usa Python Alpine, pacotes de sistema atualizados, usuário não-root
e Gunicorn. Dependências sem uso foram removidas. HIGH/CRITICAL bloqueiam,
mesmo sem correção disponível; não existe `ignore-unfixed`.
O setuptools da imagem base é atualizado pela dependência explícita
`setuptools>=83.0.0`, corrigindo o path traversal CVE-2025-47273.

Na `main`, o `GITHUB_TOKEN` publica no GHCR com `packages: write`.
PRs constroem e analisam sem publicar. O nome é
`ghcr.io/<owner>/<repo>:<commit-sha>`, com owner/repo em minúsculas.
O push precede o scan da imagem, conforme a ordem do exercício.

A imagem exata é exportada em `image.tar.gz` e usada no scan, homologação e
produção, sem novo build. O artifact da imagem dura 3 dias; aprove a produção
antes de expirar ou execute a esteira novamente.

## Aprovação e produção temporária

Por escolha para esta entrega, homologação e produção são ambientes
**temporários nos runners hospedados do GitHub**. Não há VM ou serviço
permanente. Nenhuma porta é publicada na internet. As redes Docker são
internas e os containers são removidos ao terminar; os relatórios permanecem.

O Environment `producao` exige aprovação de `Kaue-code30` e permite somente
a branch `main`. A opção de autoaprovação do autor fica permitida para o
exercício individual, mas a aprovação continua sendo uma ação manual.
Quando as etapas 1–7 passarem, abra a execução, selecione **Review deployments**,
marque `producao` e aprove. O job 8 executa no Ubuntu hospedado, carrega o
arquivo da imagem, verifica seu ID e testa `/saude` antes de publicar o relatório.
Produção é pulada em PRs e em acionamento manual fora da `main`.

O ZAP Baseline faz spider e análise passiva; não cobre integralmente todas
as rotas autenticadas ou que exigem POST. Códigos 1/2 são achados informativos;
falhas operacionais ou relatório ausente bloqueiam.

## Referências

- [Gitleaks: fingerprints e baseline](https://github.com/gitleaks/gitleaks)
- [Semgrep CLI](https://semgrep.dev/docs/cli-reference)
- [Trivy filesystem](https://trivy.dev/latest/docs/references/configuration/cli/trivy_filesystem/)
- [ZAP Baseline](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [GitHub Environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
