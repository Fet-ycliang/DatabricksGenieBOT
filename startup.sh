#!/bin/bash
# Azure App Service startup script with diagnostics
# Startup Command in Azure Portal: bash startup.sh

echo "=========================================="
echo "Startup diagnostics..."
echo "=========================================="
echo "Python: $(python3 --version 2>&1)"
echo "Working dir: $(pwd)"
echo "PORT env: ${PORT:-not set}"
echo "PYTHONPATH: ${PYTHONPATH:-not set}"

# Activate virtual environment if present
if [ -d "antenv" ]; then
    echo "Found antenv, activating..."
    source antenv/bin/activate
    echo "Python (venv): $(python3 --version 2>&1)"
    echo "Site-packages: $(python3 -c 'import site; print(site.getsitepackages()[0])' 2>&1)"
elif [ -d ".venv" ]; then
    echo "Found .venv, activating..."
    source .venv/bin/activate
fi

# Step-by-step import check with unbuffered output (-u) and timeout
echo "Testing imports (step by step)..."
python3 -u -c "
import sys, time

def timed_import(desc, stmt):
    print(f'  [{desc}] importing...', flush=True)
    t0 = time.time()
    try:
        exec(stmt)
        print(f'  [{desc}] OK ({time.time()-t0:.1f}s)', flush=True)
    except Exception as e:
        print(f'  [{desc}] FAIL ({time.time()-t0:.1f}s): {type(e).__name__}: {e}', flush=True)
        sys.exit(1)

timed_import('config',    'from app.core.config import DefaultConfig')
timed_import('exceptions','from app.core.exceptions import BotException')
timed_import('logging_mw','from app.core.logging_middleware import RequestLoggingMiddleware')
timed_import('genie_svc', 'from app.services.genie import GenieService')
timed_import('graph_svc', 'from app.services.graph import GraphService')
timed_import('bot_inst',  'from app.bot_instance import BOT, GENIE_SERVICE, SESSION_MANAGER')
timed_import('api_bot',   'from app.api.bot import router')
timed_import('api_genie', 'from app.api.genie import router')
timed_import('api_health','from app.api.health import router')
timed_import('main',      'from app.main import app')

print('All imports OK', flush=True)
" || { echo "Import failed, aborting startup"; exit 1; }

echo "=========================================="
echo "Starting uvicorn..."
echo "=========================================="

# Use PORT from Azure (default 8000), unbuffered Python output
exec python3 -u -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
