#!/usr/bin/env bash
# Autumn-only backend lifecycle. LMCache and pytest run outside these containers.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
artifact_dir="${E2E_ARTIFACTS:-e2e-artifacts}"
mkdir -p "$artifact_dir"
compose=(docker compose --project-name "${AUTUMN_COMPOSE_PROJECT:-lmcache-autumn-e2e}" -f "$script_dir/compose.yaml")

case "${1:-}" in
  start)
    docker compose version
    "${compose[@]}" up -d ps
    timeout 300 "${compose[@]}" wait bootstrap
    manager_id=$("${compose[@]}" ps -q manager)
    # A native Linux runner can reach the bridge IPs advertised by all Autumn
    # nodes. Publishing only the manager port would not expose the data path.
    manager_ip=$(docker inspect --format '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$manager_id")
    printf 'export AUTUMN_MANAGER=%q\n' "$manager_ip:9001" > "$artifact_dir/backend.env"
    ;;
  logs)
    "${compose[@]}" logs --no-color > "$artifact_dir/autumn.log" 2>&1
    "${compose[@]}" ps -a > "$artifact_dir/compose-status.txt"
    ;;
  stop)
    "${compose[@]}" down --volumes --remove-orphans
    ;;
  *)
    echo "Usage: $0 {start|logs|stop}" >&2
    exit 2
    ;;
esac
