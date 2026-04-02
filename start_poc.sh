#!/bin/bash
# start_poc.sh

# Ensure venv is activated
source venv/bin/activate

# Check if mock DB exists, create if not
if [ ! -f remedy_mock.db ]; then
    echo "Creating mock Remedy database..."
    python setup_db.py
fi

echo "🎫 Starting Remedy AI Analyst Dashboard (Streamlit)..."
streamlit run poc_app.py
