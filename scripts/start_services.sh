#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"

BACKEND_DIR="$ROOT_DIR/digital-twingo/scene-server-go"
FRONTEND_DIR="$ROOT_DIR/digital-twingo/scene-design-v2"
TRELLIS_DIR="$ROOT_DIR/TRELLIS.2"

BACKEND_PORT="${BACKEND_PORT:-9010}"
FRONTEND_PORT="${FRONTEND_PORT:-5176}"
TRELLIS_PORT="${TRELLIS_PORT:-9020}"

mkdir -p "$LOG_DIR"

is_port_open() {
  local port="$1"
  ss -ltn "sport = :$port" | awk 'NR > 1 { found = 1 } END { exit found ? 0 : 1 }'
}

wait_for_port() {
  local name="$1"
  local port="$2"
  local timeout="${3:-30}"
  local start
  start="$(date +%s)"

  while true; do
    if is_port_open "$port"; then
      echo "OK  $name is listening on port $port"
      return 0
    fi
    if (( "$(date +%s)" - start >= timeout )); then
      echo "WARN $name did not open port $port within ${timeout}s"
      return 1
    fi
    sleep 1
  done
}

start_backend() {
  if is_port_open "$BACKEND_PORT"; then
    echo "SKIP backend already running on port $BACKEND_PORT"
    return
  fi

  echo "START backend -> $BACKEND_PORT"
  (
    cd "$BACKEND_DIR"
    setsid go run SceneServerApplication.go > "$LOG_DIR/scene-server-go.log" 2>&1 < /dev/null &
    echo "$!" > "$LOG_DIR/scene-server-go.pid"
  )
  wait_for_port "backend" "$BACKEND_PORT" 45 || true
}

start_frontend() {
  if is_port_open "$FRONTEND_PORT"; then
    echo "SKIP frontend already running on port $FRONTEND_PORT"
    return
  fi

  echo "START frontend -> $FRONTEND_PORT"
  (
    cd "$FRONTEND_DIR"
    setsid npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" > "$LOG_DIR/scene-design-v2-frontend.log" 2>&1 < /dev/null &
    echo "$!" > "$LOG_DIR/scene-design-v2-frontend.pid"
  )
  wait_for_port "frontend" "$FRONTEND_PORT" 45 || true
}

start_trellis() {
  if is_port_open "$TRELLIS_PORT"; then
    echo "SKIP TRELLIS.2 already running on port $TRELLIS_PORT"
    return
  fi

  echo "START TRELLIS.2 -> $TRELLIS_PORT"
  (
    cd "$TRELLIS_DIR"
    setsid env ATTN_BACKEND=sdpa SPARSE_ATTN_BACKEND=sdpa python service/trellis2_service.py > "$LOG_DIR/trellis2-service.log" 2>&1 < /dev/null &
    echo "$!" > "$LOG_DIR/trellis2-service.pid"
  )
  wait_for_port "TRELLIS.2" "$TRELLIS_PORT" 45 || true
}

print_urls() {
  local host="${HOSTNAME:-localhost}"

  echo
  echo "Service URLs"
  echo "  Frontend:       http://127.0.0.1:${FRONTEND_PORT}/scene/"
  echo "  Frontend LAN:   http://${host}:${FRONTEND_PORT}/scene/"
  echo "  Backend Swagger http://127.0.0.1:${BACKEND_PORT}/swagger/index.html"
  echo "  Backend API:    http://127.0.0.1:${BACKEND_PORT}/sceneApi"
  echo "  TRELLIS.2 Docs: http://127.0.0.1:${TRELLIS_PORT}/docs"
  echo "  TRELLIS.2 API:  http://127.0.0.1:${TRELLIS_PORT}"
  echo
  echo "Logs"
  echo "  $LOG_DIR/scene-server-go.log"
  echo "  $LOG_DIR/scene-design-v2-frontend.log"
  echo "  $LOG_DIR/trellis2-service.log"
}

main() {
  start_backend
  start_frontend
  start_trellis
  print_urls
}

main "$@"
