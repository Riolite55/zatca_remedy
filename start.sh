#!/bin/bash
# start.sh

# Ensure venv is activated
source venv/bin/activate

# Setup database (creates app tables + imports Excel data if needed)
python setup_db.py

echo "🎫 Starting Remedy AI Support Agent (Streamlit)..."
streamlit run app.py
