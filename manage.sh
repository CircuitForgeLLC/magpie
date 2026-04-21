#!/usr/bin/env bash
# Magpie management script
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

API_PORT=8532
WEB_PORT=8531
COMPOSE="docker compose"

cmd="${1:-help}"

case "$cmd" in
  start)
    echo "Starting Magpie (API :$API_PORT, Web :$WEB_PORT)..."
    $COMPOSE up -d
    ;;
  stop)
    $COMPOSE stop
    ;;
  restart)
    $COMPOSE restart
    ;;
  status)
    $COMPOSE ps
    ;;
  logs)
    service="${2:-}"
    if [[ -n "$service" ]]; then
      $COMPOSE logs -f "$service"
    else
      $COMPOSE logs -f
    fi
    ;;
  build)
    $COMPOSE build
    ;;
  open)
    xdg-open "http://localhost:$WEB_PORT" 2>/dev/null || open "http://localhost:$WEB_PORT"
    ;;
  dev-api)
    echo "Starting API in dev mode (host network, port $API_PORT)..."
    conda run -n cf uvicorn app.main:app --host 0.0.0.0 --port $API_PORT --reload
    ;;
  dev-web)
    echo "Starting frontend dev server (port $WEB_PORT)..."
    cd frontend && npm run dev
    ;;
  login)
    echo "Refreshing Reddit session..."
    conda run -n cf xvfb-run --auto-servernum python -m app.services.reddit.post --login
    ;;
  migrate)
    echo "Running DB migrations..."
    conda run -n cf python -c "from app.db.store import Store; from app.core.config import get_settings; s=Store(get_settings().db_path); s.run_migrations(); s.close(); print('Done.')"
    ;;
  help|*)
    echo "Usage: ./manage.sh <command>"
    echo ""
    echo "Commands:"
    echo "  start       Start all services via Docker Compose"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show service status"
    echo "  logs [svc]  Tail logs (optionally for one service)"
    echo "  build       Build Docker images"
    echo "  open        Open browser to dashboard"
    echo "  dev-api     Run API in dev mode (conda, hot-reload)"
    echo "  dev-web     Run frontend dev server"
    echo "  login       Refresh Reddit Playwright session"
    echo "  migrate     Run DB migrations standalone"
    ;;
esac
