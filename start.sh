#!/bin/bash
# start.sh

# Ensure venv is activated
source venv/bin/activate

echo "🚀 Starting Mock Remedy Server on http://localhost:8080..."
python mock_remedy.py &
MOCK_PID=$!

# Give the mock server a second to boot up
sleep 2

echo "🎫 Starting Remedy AI Agent UI (Streamlit)..."
streamlit run app.py

# When streamlit exits, kill the mock server
echo "🛑 Shutting down Mock Remedy Server..."
kill $MOCK_PID
