V
# ==============================

export PATH=$PATH:/usr/local/bin

# ==============================
# PROJECT ALIASES
# ==============================

alias run_api="cd ~/indlab-techtrends-ds && source venv/bin/activate && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001"

alias run_dash="cd ~/indlab-techtrends-ds && source venv/bin/activate && python -m streamlit run src/dashboard/app.py --server.address 0.0.0.0 --server.port 8506"

alias stop_all="pkill -f streamlit && pkill -f uvicorn"           


