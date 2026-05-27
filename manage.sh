#!/usr/bin/env bash
# Magpie management script — native dev process manager
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# ------------------------------------------------------------------ #
# Config
# ------------------------------------------------------------------ #

API_PORT=8532
WEB_PORT=8531
CONDA_ENV=cf
DATA_DIR="${HOME}/.local/share/magpie"
LOG_DIR="${DATA_DIR}/logs"
PID_API="${DATA_DIR}/api.pid"
PID_WEB="${DATA_DIR}/web.pid"
LOG_API="${LOG_DIR}/api.log"
LOG_WEB="${LOG_DIR}/web.log"

mkdir -p "$DATA_DIR" "$LOG_DIR"

# ------------------------------------------------------------------ #
# Colors
# ------------------------------------------------------------------ #

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }
err()  { echo -e "${RED}✗${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }

# ------------------------------------------------------------------ #
# Process helpers
# ------------------------------------------------------------------ #

_pid_alive() {
    local pid_file="$1"
    [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

_port_open() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " || \
    lsof -ti:"$1" >/dev/null 2>&1
}

_start_api() {
    if _pid_alive "$PID_API"; then
        warn "API already running (PID $(cat "$PID_API"))"
        return
    fi
    if _port_open "$API_PORT"; then
        warn "Port :${API_PORT} already in use by another process — stop it first or change API_PORT"
        return
    fi
    info "Starting API on :${API_PORT}..."
    conda run --no-capture-output -n "$CONDA_ENV" \
        uvicorn app.main:app \
            --host 0.0.0.0 --port "$API_PORT" \
            --reload --reload-dir app \
        >> "$LOG_API" 2>&1 &
    echo $! > "$PID_API"
    # Wait for port to open (up to 10s)
    local i=0
    while ! _port_open "$API_PORT" && (( i++ < 20 )); do sleep 0.5; done
    if _port_open "$API_PORT"; then
        ok "API up → http://localhost:${API_PORT}/docs"
    else
        warn "API started (PID $(cat "$PID_API")) but port not open yet — check: ./manage.sh logs api"
    fi
}

_start_web() {
    if _pid_alive "$PID_WEB"; then
        warn "Web already running (PID $(cat "$PID_WEB"))"
        return
    fi
    if _port_open "$WEB_PORT"; then
        warn "Port :${WEB_PORT} already in use by another process — stop it first or change WEB_PORT"
        return
    fi
    info "Starting web on :${WEB_PORT}..."
    cd frontend
    npm run dev >> "$LOG_WEB" 2>&1 &
    echo $! > "$PID_WEB"
    cd "$REPO_DIR"
    local i=0
    while ! _port_open "$WEB_PORT" && (( i++ < 20 )); do sleep 0.5; done
    if _port_open "$WEB_PORT"; then
        ok "Web up → http://localhost:${WEB_PORT}"
    else
        warn "Web started (PID $(cat "$PID_WEB")) but port not open yet — check: ./manage.sh logs web"
    fi
}

_stop_service() {
    local name="$1" pid_file="$2"
    if _pid_alive "$pid_file"; then
        local pid
        pid=$(cat "$pid_file")
        info "Stopping ${name} (PID ${pid})..."
        kill "$pid" 2>/dev/null || true
        # Give it up to 5s to exit
        local i=0
        while _pid_alive "$pid_file" && (( i++ < 10 )); do sleep 0.5; done
        if _pid_alive "$pid_file"; then
            warn "${name} didn't stop cleanly — sending SIGKILL"
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
        ok "${name} stopped"
    else
        rm -f "$pid_file"
        info "${name} was not running"
    fi
}

# ------------------------------------------------------------------ #
# Commands
# ------------------------------------------------------------------ #

cmd="${1:-help}"
shift || true

case "$cmd" in

  start)
    _start_api
    _start_web
    ;;

  stop)
    _stop_service "API" "$PID_API"
    _stop_service "Web" "$PID_WEB"
    ;;

  restart)
    _stop_service "API" "$PID_API"
    _stop_service "Web" "$PID_WEB"
    _start_api
    _start_web
    ;;

  restart-api)
    _stop_service "API" "$PID_API"
    _start_api
    ;;

  restart-web)
    _stop_service "Web" "$PID_WEB"
    _start_web
    ;;

  status)
    echo ""
    echo -e "  ${CYAN}Magpie — Service Status${RESET}"
    echo "  ─────────────────────────────────────"

    # API
    if _pid_alive "$PID_API"; then
        local_pid=$(cat "$PID_API")
        if _port_open "$API_PORT"; then
            ok "  API       :${API_PORT}  (PID ${local_pid})"
        else
            warn "  API       PID ${local_pid} alive but port :${API_PORT} not open"
        fi
    else
        err "  API       stopped"
    fi

    # Web
    if _pid_alive "$PID_WEB"; then
        local_pid=$(cat "$PID_WEB")
        if _port_open "$WEB_PORT"; then
            ok "  Web       :${WEB_PORT}  (PID ${local_pid})"
        else
            warn "  Web       PID ${local_pid} alive but port :${WEB_PORT} not open"
        fi
    else
        err "  Web       stopped"
    fi

    # Scheduler (query API)
    if _port_open "$API_PORT"; then
        sched=$(curl -sf "http://localhost:${API_PORT}/api/v1/scheduler/status" \
                | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d.get('job_count',0)} job(s)\")" 2>/dev/null || echo "?")
        info "  Scheduler ${sched} scheduled"
    fi

    # Session age
    SESSION_FILE="${DATA_DIR}/session.json"
    if [[ -f "$SESSION_FILE" ]]; then
        age_h=$(python3 -c "import time,os; print(f\"{(time.time()-os.path.getmtime('$SESSION_FILE'))/3600:.1f}h\")" 2>/dev/null || echo "?")
        if python3 -c "import time,os; exit(0 if (time.time()-os.path.getmtime('$SESSION_FILE'))/3600 < 12 else 1)" 2>/dev/null; then
            ok "  Session   ${age_h} old (valid)"
        else
            warn "  Session   ${age_h} old (stale — run: ./manage.sh login)"
        fi
    else
        warn "  Session   no session.json — run: ./manage.sh login"
    fi

    echo ""
    ;;

  logs)
    target="${1:-all}"
    case "$target" in
      api)  tail -f "$LOG_API" ;;
      web)  tail -f "$LOG_WEB" ;;
      all|*)
        echo "=== API log ===" && tail -f "$LOG_API" &
        echo "=== Web log ===" && tail -f "$LOG_WEB" &
        wait
        ;;
    esac
    ;;

  open)
    xdg-open "http://localhost:${WEB_PORT}" 2>/dev/null \
      || open "http://localhost:${WEB_PORT}" 2>/dev/null \
      || info "Open http://localhost:${WEB_PORT} in your browser"
    ;;

  update)
    info "Pulling latest changes..."
    git pull

    info "Installing Python deps..."
    conda run -n "$CONDA_ENV" pip install -q -e .

    info "Installing frontend deps..."
    cd frontend && npm install --silent && cd "$REPO_DIR"

    # Restart API to pick up code changes; web hot-reloads itself
    if _pid_alive "$PID_API"; then
        info "Restarting API to pick up changes..."
        _stop_service "API" "$PID_API"
        _start_api
    else
        info "API not running — start with: ./manage.sh start"
    fi
    ok "Update complete"
    ;;

  build)
    # Build the frontend SPA for production serving on menagerie.circuitforge.tech/magpie
    # VITE_BASE_URL must end with / so Vite generates correct asset paths.
    info "Building frontend for /magpie/ path prefix..."
    cd frontend && VITE_BASE_URL=/magpie/ npm run build && cd ..
    ok "Build complete → frontend/dist/ (base=/magpie/)"
    info "Serving: ./manage.sh serve"
    ;;

  serve)
    # Serve the pre-built frontend dist at port WEB_PORT using a simple static file server.
    # In production, Caddy proxies menagerie.circuitforge.tech/magpie* → this port.
    info "Serving pre-built frontend on :${WEB_PORT} ..."
    conda run --no-capture-output -n "$CONDA_ENV" \
        python -m http.server "$WEB_PORT" --directory frontend/dist >> "$LOG_WEB" 2>&1 &
    echo $! > "$PID_WEB"
    ok "Static server up → http://localhost:${WEB_PORT}"
    ;;

  migrate-sessions)
    info "Migrating session.json → sessions/ directory..."
    conda run -n "$CONDA_ENV" python scripts/migrate_sessions.py
    ;;

  login)
    info "Refreshing Reddit session (opens browser via Xvfb)..."
    REDDIT_SESSION_FILE="${DATA_DIR}/sessions/alan_reddit.json" \
        conda run --no-capture-output -n "$CONDA_ENV" \
        xvfb-run --auto-servernum \
        python -m app.services.reddit.post --login
    ;;

  migrate)
    info "Running DB migrations..."
    conda run -n "$CONDA_ENV" python - <<'EOF'
from app.db.store import Store
from app.core.config import get_settings
s = Store(get_settings().db_path)
s.run_migrations()
s.close()
print("Migrations applied.")
EOF
    ;;

  seed)
    info "Seeding campaigns from legacy reddit-poster scripts..."
    conda run -n "$CONDA_ENV" python scripts/seed_campaigns.py
    ;;

  help|*)
    echo ""
    echo -e "  ${CYAN}Usage: ./manage.sh <command> [args]${RESET}"
    echo ""
    echo "  Process control:"
    echo "    start          Start API and web dev server in background"
    echo "    stop           Stop both"
    echo "    restart        Full restart"
    echo "    restart-api    Restart API only (e.g. after code changes)"
    echo "    restart-web    Restart web dev server only"
    echo "    status         Show process status, scheduler jobs, session age"
    echo ""
    echo "  Logs:"
    echo "    logs           Tail all logs"
    echo "    logs api       Tail API log only"
    echo "    logs web       Tail web log only"
    echo "    Logs at: ${LOG_DIR}/"
    echo ""
    echo "  Maintenance:"
    echo "    update           git pull + pip/npm install + API restart"
    echo "    migrate          Run DB migrations standalone"
    echo "    migrate-sessions Move session.json → sessions/alan_reddit.json"
    echo "    seed             Seed campaigns from legacy scripts"
    echo "    login            Refresh Reddit Playwright session"
    echo "    build            Build frontend for menagerie (/magpie/ base path)"
    echo "    serve            Serve pre-built frontend dist on :${WEB_PORT}"
    echo "    open             Open dashboard in browser"
    echo ""
    ;;
esac
