#!/bin/bash
# Azure App Service startup script with diagnostics
# Set this as the startup command in Azure Portal:
#   bash startup.sh

echo "=========================================="
echo "Startup diagnostics..."
echo "=========================================="
echo "Python: $(python3 --version 2>&1)"
echo "Working dir: $(pwd)"
echo "PORT env: ${PORT:-not set}"

# Quick import check — catches missing dependencies early
echo "Testing imports..."
python3 -c "
import sys
try:
    from app.main import app
    print('OK: app.main imported successfully')
except Exception as e:
    print(f'FAIL: {type(e).__name__}: {e}', file=sys.stderr)
    sys.exit(1)
" || { echo "Import failed, aborting startup"; exit 1; }

echo "=========================================="
echo "Starting uvicorn..."
echo "=========================================="

# Use PORT from Azure (default 8000)
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
