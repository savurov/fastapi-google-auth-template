# Init:
```
uv sync
uv run pre-commit install
```

# Start:
```
docker compose up
```

# Pre-commit checks:
```
uv run pre-commit
```

# Coverage:
```
uv run pytest tests --cov=src
```


# Migrations:
```
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "<migration_name>" --rev-id "<revision_id>"
```

# PSQL:
```
docker compose exec db psql -U local -d local
```

# GoogleAuth
1) open https://console.cloud.google.com/ and create New Project
2) APIs & Services > Credentials > Configure consent screen > Get started
(fill app name, email, choose external audience)
3) Clients > Create client
Application type: Web application
Authorized JavaScript origins: http://localhost:5173 (frontend uri)
Authorized redirect URIs: http://localhost:5173/api/v1/auth/google/callback (backend callback: vite proxy in this example)
5) update .env file with
```
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-secret>
GOOGLE_REDIRECT_URI=<your-redirect-uri>
```
