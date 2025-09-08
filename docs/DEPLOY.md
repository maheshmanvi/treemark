# === FILE: docs/DEPLOY.md ===
# Deploying TreeMark API (optional)

1. Use the included FastAPI app at tree_mark.api.server:app
2. Run with Uvicorn for production style serving (example):
   - uvicorn tree_mark.api.server:app --host 0.0.0.0 --port 8000 --workers 4