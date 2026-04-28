#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# J.A.R.V.I.S. Desktop Launcher — macOS / Linux
# ══════════════════════════════════════════════════════════════

set -e

echo ""
echo " ================================================"
echo "  J.A.R.V.I.S. Desktop - AI Personal Assistant"
echo " ================================================"
echo ""

DEV_MODE=0
NO_WAKE=""

for arg in "$@"; do
  case "$arg" in
    --dev)     DEV_MODE=1 ;;
    --no-wake) NO_WAKE="--no-wake" ;;
  esac
done

# ── Check prerequisites ──────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo " [ERROR] Python3 not found. Install Python 3.10+"
  exit 1
fi

if ! command -v node &>/dev/null; then
  echo " [ERROR] Node.js not found. Install Node.js 18+"
  exit 1
fi

# ── Check .env file ──────────────────────────────────────────
if [ ! -f "jarvis/.env" ]; then
  echo " [WARN] No .env file found. Copying from .env.example..."
  cp jarvis/.env.example jarvis/.env 2>/dev/null || true
  echo "        Edit jarvis/.env and add your GROQ_API_KEY."
  echo ""
fi

# ── Python backend ───────────────────────────────────────────
echo " [1/2] Starting Python backend..."
cd jarvis
python3 main.py $NO_WAKE &
BACKEND_PID=$!
cd ..

echo " [....] Waiting for backend to boot (5s)..."
sleep 5

# ── HUD Frontend ─────────────────────────────────────────────
echo " [2/2] Starting HUD frontend..."
cd jarvis-hud

if [ ! -d "node_modules" ]; then
  echo " [....] Installing HUD dependencies..."
  npm install
fi

if [ "$DEV_MODE" -eq 1 ]; then
  echo " [DEV]  Starting in browser-only mode..."
  npm run dev &
  sleep 3
  if command -v open &>/dev/null; then
    open "http://localhost:5173"
  elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5173"
  fi
else
  echo " [PROD] Starting Electron HUD..."
  npm run dev &
  sleep 3
  npx electron . &
fi

cd ..

echo ""
echo " ================================================"
echo "  All systems launched."
echo "  Backend: ws://localhost:6789"
echo "  HUD:     http://localhost:5173"
echo " ================================================"
echo ""
echo "  Flags:"
echo "    --dev      Browser-only mode (no Electron)"
echo "    --no-wake  Skip clap detection (dev testing)"
echo ""

# Wait for backend process
wait $BACKEND_PID
