#!/usr/bin/env bash
set -e

# Start the FastAPI backend on port 8000
echo "Starting backend..."
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd ..

# Wait for backend to start
sleep 2

# Start the Next.js standalone server on PORT (provided by Render, e.g. 10000)
# Ensure Next.js binds to 0.0.0.0
export HOSTNAME="0.0.0.0"
export INTERNAL_API_URL="http://127.0.0.1:8000"
echo "Starting frontend on port ${PORT:-3000}..."
node frontend/server.js
