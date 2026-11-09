# Esteira DevSecOps

O workflow [esteira.yml](../.github/workflows/esteira.yml) executa em pushes
na `main`, pull requests destinados à `main` e acionamento manual no Actions.
Os jobs são sequenciais: qualquer falha bloqueia as próximas etapas.
`Resumo da Esteira` usa `if: always()`, recebe o resultado dos oito jobs e
publica a tabela no Job Summary e no artifact `resumo-da-esteira`, inclusive
quando um scanner bloqueia a execução. O cancelamento de toda a execução
ou indisponibilidade do GitHub pode impedir até mesmo esse job.

| Etapa | Ferramenta | Artifact | Gate |
| --- | --- | --- | --- |
| 1. Secrets | Gitleaks no histórico completo | `relatorio-01-gitleaks` | Qualquer segredo ou erro bloqueia |
| 2. SAST | Semgrep, regras de `regras-banco/` | `relatorio-02-semgrep` | Qualquer achado ou erro bloqueia |
| 3. Build | Python 3.12, pip, compileall, unittest, tar | `relatorio-03-build` | Instalação, conflitos, sintaxe ou testes falhando bloqueiam |
| 4. SCA | Trivy fs nas dependências resolvidas | `relatorio-04-trivy-sca` | HIGH/CRITICAL bloqueiam, mesmo sem correção disponível |
| 5. Imagem | Docker Buildx e GHCR | `relatorio-05-docker-build` | Falha de build, exportação ou push bloqueia |
| 6. Scan da imagem | Trivy image | `relatorio-06-trivy-image` | HIGH/CRITICAL bloqueiam, mesmo sem correção disponível |
| 7. Homologação e DAST | Docker e OWASP ZAP Baseline | `relatorio-07-homologacao-zap` | Achados informativos; indisponibilidade da aplicação ou erro do scanner bloqueia |
| 8. Produção | GitHub Environment `producao` e Docker | `relatorio-08-producao` | Aprovação manual e health check |

Os relatórios são enviados com `if: always()` nos jobs que chegaram a
executar. Etapas puladas (`skipped`) não produzem artifacts. Falhas anteriores
à criação dos relatórios, como erro no checkout, podem deixar um job sem artifact.
O Gitleaks mascara os segredos nos relatórios e nos logs.

O arquivo `.gitleaksignore` documenta uma exceção por fingerprint para um
falso positivo confirmado: o rótulo da tabela jq no commit `2157341` foi
interpretado como chave de API. O rótulo foi alterado, e a exceção cobre
somente aquela ocorrência no histórico, sem excluir o workflow do scanner.

## Build e publicação

O build instala as dependências em um virtualenv limpo, executa `pip check`,
compila o código e testa `/saude`, resposta 404 e login inválido. As versões
efetivamente instaladas são registradas em `requirements-resolved.txt`.
O pacote `app.tar.gz` inclui essas versões e é verificado por SHA-256 antes
do Docker build. O Trivy fs analisa esse mesmo conjunto resolvido, incluindo
dependências transitivas. Como existem intervalos em `requirements.txt`,
execuções diferentes ainda podem resolver versões diferentes.

A imagem recebe a tag `ghcr.io/<owner>/<repo>:<commit-sha>` em letras minúsculas.
Em PRs ela é construída e analisada sem publicação. Na `main`, inclusive em
acionamento manual, o push usa o `GITHUB_TOKEN` com `packages: write`.
Habilite GitHub Actions no repositório e permita a criação/escrita do package
no GHCR; para um package existente, conceda acesso ao repositório em
**Package settings → Manage Actions access**.

A ordem solicitada faz o push antes do scan da imagem. Uma imagem publicada
pode ser reprovada na etapa 6 e não chegar à homologação/produção.
O artifact da etapa 5 transporta a imagem exata construída para o scan,
homologação e produção; não há novo build nem resolução de tag no deploy.
Esse artifact é grande e tem retenção de 3 dias. Aprove o deploy antes de
expirar; depois disso, execute novamente a esteira.

As versões dos scanners estão fixadas no bloco `env` do workflow, e as
actions estão fixadas por versão principal. Atualize-as de forma controlada;
as bases de vulnerabilidades do Trivy continuam sendo baixadas a cada scan.

## Homologação isolada

A etapa 7 cria um ambiente temporário no runner hospedado do GitHub. A rede
Docker `--internal` não tem portas publicadas e é removida após o scan.
O ZAP acessa `http://app-homologacao:5000` nessa rede e grava HTML, JSON, logs
e código de saída. Os códigos 1 e 2 representam achados e são informativos;
código 3 ou ausência do relatório representa falha operacional e bloqueia.
A aplicação precisa responder em `/saude` antes do scan.

O Baseline faz descoberta de URLs e análise passiva. Rotas que exigem login,
POST ou parâmetros específicos não têm cobertura completa. As regras
existentes em `.zap/rules.tsv` são aproveitadas; essa configuração não
transforma o Baseline em um scan ativo.

## Configurar aprovação e produção do laboratório

O projeto contém vulnerabilidades didáticas. O destino implementado é uma
VM isolada do laboratório, com acesso somente em `127.0.0.1:5000`. O job usa
o nome `producao` para representar a etapa do exercício. Não exponha essa
aplicação na internet, conforme as orientações do README.

1. Em **Settings → Environments**, crie `producao`. Configure **Required
   reviewers**, marque **Prevent self-review** e restrinja deployments à
   branch `main`. Verifique se seu plano/visibilidade do repositório permite
   revisores obrigatórios. Apenas declarar `environment: producao` no YAML
   não cria uma regra de aprovação.
2. Prepare uma VM Linux exclusiva do laboratório com Docker, Bash e Python 3,
   e registre um runner do repositório com labels `self-hosted`, `linux`,
   `producao-lab`. O usuário do runner precisa conseguir executar Docker.
   Esse runner somente recebe o job de produção da `main`, após aprovação.
3. Na VM, crie `/opt/pipeline/producao.env` fora do checkout, com permissões
   restritas ao usuário do runner. Configure `SECRET_KEY`, `DB_HOST`,
   `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `API_KEY_BANDEIRA` com valores do
   laboratório. Não versione esse arquivo.
4. Só depois de configurar revisores e runner, crie a variável do
   **repositório** `ENABLE_PRODUCTION` com valor `true` em **Settings →
   Secrets and variables → Actions → Variables**. Sem ela, a etapa 8 é
   pulada. Não use uma variável restrita ao Environment para esse controle,
   pois a condição do job precisa ser avaliada antes de acessar o ambiente.
5. Envie as alterações para `main` ou execute o workflow manualmente nessa
   branch. Após as etapas anteriores passarem, aprove em **Review deployments**.

O script `scripts/deploy-lab.sh` carrega a imagem aprovada e usa seu ID do
Docker registrado no build. Substitui o container `simulador-cartoes`,
valida `/saude` e restaura o anterior se a inicialização falhar. Há uma breve
interrupção durante a troca. O container anterior fica parado como
`simulador-cartoes-anterior`; revise e remova esse backup antes do próximo
deploy. Não há migração, provisionamento de banco ou persistência de dados
da aplicação nesse exemplo. O servidor Flask e as vulnerabilidades da
aplicação continuam sendo os do laboratório.

## Primeira execução e bloqueios esperados

O código ainda contém `eval`, `pickle.loads` e MD5 detectados pelas regras
locais. O histórico Git também pode conter segredos já removidos do código.
Portanto, a primeira execução pode parar no Gitleaks ou Semgrep: isso é o
gate funcionando. Corrija os achados para avançar; não foi adicionado bypass
dos scanners para fazer o projeto vulnerável chegar ao fim.

Para exigir a esteira antes do merge, configure a proteção/ruleset da `main`
com os checks de 1 a 7. O resumo é informativo e não substitui esses checks.
Configurar somente o resumo como obrigatório permitiria aprovar um PR cujo
scanner falhou, já que o job de resumo conclui após registrar a falha.

## Referências

- [Gitleaks: comandos e relatórios](https://github.com/gitleaks/gitleaks)
- [Semgrep: CLI e códigos de saída](https://semgrep.dev/docs/cli-reference)
- [Trivy filesystem](https://trivy.dev/latest/docs/references/configuration/cli/trivy_filesystem/)
- [ZAP Baseline: relatórios e códigos de saída](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [GitHub Environments e disponibilidade de regras de proteção](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
