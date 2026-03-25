#!/bin/bash
# KubeDojo - Documentation Server (Starlight/Astro)
# Starts Astro dev server on port 4321

set -e

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting KubeDojo Documentation Server..."
echo "Project: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Port to use
PORT=4321
LOG_FILE="/tmp/astro-kubedojo.log"

# Check if port is in use
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "Port $PORT is already in use"
    echo "   Killing existing process..."
    lsof -ti:$PORT | xargs kill -9
    sleep 1
    echo "Cleaned up port $PORT"
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo "Dependencies installed"
else
    echo "Dependencies found"
fi

# Start Astro dev server
echo "Starting Astro dev server on http://localhost:$PORT"
nohup npx astro dev --port $PORT > "$LOG_FILE" 2>&1 &
DEV_PID=$!
sleep 3

# Check if it started successfully
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "Astro dev server running (PID: $DEV_PID)"
    echo "   Documentation: http://localhost:$PORT"
    echo "   Logs: $LOG_FILE"
    echo ""
    echo "To stop: kill $DEV_PID"
    echo "Or: lsof -ti:$PORT | xargs kill"
else
    echo "Astro dev server failed to start"
    echo "   Check logs: $LOG_FILE"
    exit 1
fi
