#!/usr/bin/env bash
# Deploy temporário para o exercício, após aprovação do Environment.
set -euo pipefail

archive=${1:?Informe o arquivo da imagem aprovada}
docker load -i "$archive"
image_id=$(python3 -c 'import json; print(json.load(open("image/image.json"))[0]["Id"])')
docker image inspect "$image_id" >/dev/null
docker network create --internal producao-lab
docker run -d --name simulador-cartoes --network producao-lab \
  --cap-drop ALL --security-opt no-new-privileges \
  -e SECRET_KEY="$(openssl rand -hex 32)" "$image_id"

for attempt in $(seq 1 30); do
  if docker exec simulador-cartoes python -c \
    'import urllib.request; r=urllib.request.urlopen("http://127.0.0.1:5000/saude", timeout=2); assert r.status == 200' ; then
    echo "Deploy temporário validado: $image_id"
    docker inspect --format '{{.Image}} {{.State.Status}}' simulador-cartoes > reports/deploy.txt
    exit 0
  fi
  sleep 2
done
echo 'Health check de produção falhou.'
exit 1
