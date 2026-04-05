#!/bin/bash
# start_poc.sh

# Ensure venv is activated
source venv/bin/activate

# Setup database (creates app tables + imports Excel data if needed)
python setup_db.py

echo "🎫 Starting Remedy AI Analyst Dashboard (Streamlit)..."
streamlit run poc_app.py
