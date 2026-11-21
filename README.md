# LinkSnap API (Flask)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py            # runs on http://localhost:5000
pytest                   # run the API tests
```

Environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | Port to listen on | `5000` |
| `LINKSNAP_DB` | SQLite file path | `backend/linksnap.db` |
| `LINKSNAP_PUBLIC_URL` | Base used in generated short links | request host |
| `LINKSNAP_CORS_ORIGINS` | Allowed frontend origins | `*` |

The frontend reads `VITE_API_BASE_URL` (default `http://localhost:5000`).
