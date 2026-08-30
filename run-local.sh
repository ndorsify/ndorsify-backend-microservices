#!/usr/bin/env bash
# Run all Ndorsify services locally on SQLite (no Postgres/Docker needed).
# Ports match ndorsify-app/src/lib/config.js. Logs + pids under .run/.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/.venv-run/bin/activate"
RUN="$ROOT/.run"
mkdir -p "$RUN"

# Allow the served frontend (:5055) and the CRA dev server (:3000).
export CORS_ORIGINS="http://localhost:5055,http://localhost:3000"
# Dev convenience: users-service echoes verify/reset tokens in responses.
export EXPOSE_DEV_TOKENS="true"

# service-dir : port
services=(
  "users-service:1000"
  "dynamic-content-service:5000"
  "profile-service:6060"
  "messaging-service:3000"
  "discovery-service:9000"
  "campaign-service:2000"
  "collaboration-service:4000"
)

for entry in "${services[@]}"; do
  name="${entry%%:*}"; port="${entry##*:}"
  dir="$ROOT/microservices/$name"
  db="$dir/run.sqlite3"
  ( cd "$dir" && \
    PORT="$port" \
    DATABASE_URL="sqlite+aiosqlite:///$db" \
    nohup python -m app.server >"$RUN/$name.log" 2>&1 & echo $! > "$RUN/$name.pid" )
  echo "started $name on :$port (pid $(cat "$RUN/$name.pid"))"
done
echo "logs: $RUN/*.log"
