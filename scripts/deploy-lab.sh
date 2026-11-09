#!/usr/bin/env bash
# Executado somente no runner dedicado do laboratório, após aprovação.
set -euo pipefail

archive=${1:?Informe o arquivo da imagem aprovada}
name=simulador-cartoes
previous="${name}-anterior"
env_file=/opt/pipeline/producao.env

test -s "$env_file" || { echo "Configure $env_file no runner"; exit 1; }
docker load -i "$archive"
# A imagem transportada é identificada pelo ID registrado no build, sem
# depender de uma tag mutável do registry.
image_id=$(python3 -c 'import json; print(json.load(open("image/image.json"))[0]["Id"])')
docker image inspect "$image_id" >/dev/null
if docker container inspect "$previous" >/dev/null 2>&1; then
  echo "Existe $previous de um deploy anterior. Revise/remova esse backup antes de continuar."
  exit 1
fi
had_previous=false
if docker container inspect "$name" >/dev/null 2>&1; then
  docker stop "$name"
  docker rename "$name" "$previous"
  had_previous=true
fi

rollback() {
  docker logs "$name" 2>&1 || true
  docker rm -f "$name" >/dev/null 2>&1 || true
  if [ "$had_previous" = true ]; then
    docker rename "$previous" "$name"
    docker start "$name"
  fi
}
trap rollback ERR

docker run -d --name "$name" --restart unless-stopped \
  --env-file "$env_file" --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:5000:5000 "$image_id"
for attempt in $(seq 1 30); do
  if docker exec "$name" python -c \
    'import urllib.request; urllib.request.urlopen("http://127.0.0.1:5000/saude", timeout=2)' ; then
    trap - ERR
    echo "Deploy validado: $image_id (127.0.0.1:5000)"
    if [ "$had_previous" = true ]; then
      echo "Backup parado: $previous; revise e remova antes do próximo deploy."
    fi
    exit 0
  fi
  sleep 2
done
echo 'Health check falhou; restaurando versão anterior.'
false
