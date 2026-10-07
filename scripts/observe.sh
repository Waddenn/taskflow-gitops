#!/usr/bin/env bash
# Échantillonne le Service depuis le cluster (pas de port-forward vers un seul pod).
# Usage : ./scripts/observe.sh [service] [nombre] [chemin]
set -euo pipefail
source "$(dirname "$0")/check-context.sh"
SERVICE="${1:-taskflow}"
COUNT="${2:-40}"
HTTP_PATH="${3:-/}"
[[ "$SERVICE" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ && ${#SERVICE} -le 63 ]] || { echo 'Service invalide' >&2; exit 2; }
[[ "$COUNT" =~ ^[1-9][0-9]{0,3}$ ]] || { echo 'Nombre attendu : 1 à 9999' >&2; exit 2; }
[[ "$HTTP_PATH" =~ ^/[a-zA-Z0-9/_-]*$ ]] || { echo 'Chemin HTTP invalide' >&2; exit 2; }
echo "$(date -u +%FT%TZ) service=$SERVICE nombre=$COUNT chemin=$HTTP_PATH"
kubectl -n taskflow run "observe-$(date +%s)-$RANDOM" --rm -i --restart=Never --quiet \
  --image=curlimages/curl:8.12.1 --command -- sh -c '
service="$1"; count="$2"; path="$3"
for i in $(seq 1 "$count"); do
  r=$(curl -s --connect-timeout 2 -m 5 -H "Connection: close" -w " %{http_code}" "http://${service}${path}") || true
  v=$(printf "%s" "$r" | sed -n '\''s/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'\'')
  echo "version=${v:-aucune} http=${r##* }"
done | sort | uniq -c' sh "$SERVICE" "$COUNT" "$HTTP_PATH"
