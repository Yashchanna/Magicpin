# Magicpin

## Public deployment

The evaluator needs a publicly reachable bot URL, not the GitHub repo URL.

Deploy the FastAPI app from the repository root using either:

1. Docker: build the included [Dockerfile](Dockerfile) and expose the container on the platform's public HTTPS URL.
2. Procfile-based hosting: run `uvicorn bot.main:app --host 0.0.0.0 --port ${PORT:-8080}` from the repo root.

The bot must respond to these endpoints on the public base URL:

1. `GET /v1/healthz`
2. `GET /v1/metadata`
3. `POST /v1/context`
4. `POST /v1/tick`
5. `POST /v1/reply`

