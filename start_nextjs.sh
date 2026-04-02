#!/bin/bash
# start_nextjs.sh

# Ensure venv is activated for backend
source venv/bin/activate

# Check if mock DB exists, create if not
if [ ! -f remedy_mock.db ]; then
    echo "Creating mock Remedy database..."
    python setup_db.py
fi

echo "🚀 Starting FastAPI Backend on http://localhost:8000..."
uvicorn api:app --port 8000 &
BACKEND_PID=$!

sleep 2

echo "🎫 Starting Next.js Frontend on http://localhost:3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Trap SIGINT (Ctrl+C) and kill background processes
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID" SIGINT

# Wait for both background processes
wait $BACKEND_PID $FRONTEND_PID
