#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# 0) Activate the conda env that contains SurrealDB, Poetry & Streamlit${CDSW_APP_PORT}
# ---------------------------------------------------------------------------
eval "$(conda shell.bash hook)"
conda activate open-notebook

# ---------------------------------------------------------------------------
# 1) Start SurrealDB on the writable port (APP_PORT) in the background
# ---------------------------------------------------------------------------
/home/cdsw/.surrealdb/surreal start \
  --user root \
  --pass root \
  --bind 127.0.0.1:8080 \
  rocksdb://mydata/mydatabase.db &
SURREAL_PID=$!

# ---------------------------------------------------------------------------
# 2) Start Streamlit on the read‑only port (READONLY_PORT)
# ---------------------------------------------------------------------------
poetry run streamlit run /home/cdsw/app_home.py \
  --server.port ${CDSW_READONLY_PORT} \
  --server.address 127.0.0.1 \
  --server.headless true \
  --global.developmentMode false \
  --browser.gatherUsageStats false &

# ---------------------------------------------------------------------------
# 3) Keep the container alive as long as either process is running
# ---------------------------------------------------------------------------
wait -n "${SURREAL_PID}"
