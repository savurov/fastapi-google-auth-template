## About

This is a production-ready FastAPI template with Google OAuth authentication,
using a simple JWT-in-cookie approach after the Google OAuth flow.

A minimal React frontend for testing this backend is available here:
https://github.com/savurov/react-google-auth-template

The project comes with a full quality and CI setup out of the box:
- **Ruff** for linting and formatting
- **Mypy (strict mode)** for static type checking
- **Pytest** with coverage reporting
- **Pre-commit hooks** for local checks
- **GitHub Actions CI** running all quality checks on every push

All checks are configurable.
For example, strict type checking can be disabled in `pyproject.toml` if needed:
```toml
[tool.mypy]
strict = false
```

Coverage thresholds can also be adjusted or removed:
```toml
[tool.coverage.report]
fail_under = 100
```

Unused or unnecessary linting rules can be removed from:
```toml
[tool.ruff.lint]
```

This template is designed to be **easy to customize**, while keeping strong defaults for production use.

---

## Requirements
- Docker + Docker Compose
- Python 3.12+
- uv

---

## How to run locally
```bash
uv sync
uv run pre-commit install
```

Start the app:
```bash
docker compose up
```

---

## Tools

You can run any installed tool using:
```bash
uv run <command>
```

Examples: `pre-commit`, `ruff`, `mypy`, etc.

### Tests
```bash
uv run pytest
uv run pytest --cov=src    # coverage check
```

### Migrations
```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "<migration_name>" --rev-id "<revision_id>"
```

### PostgreSQL
```bash
docker compose exec db psql -U local -d local
```

---

## Google OAuth (local)

1. Open https://console.cloud.google.com and create a **new project**
2. Go to **APIs & Services → Credentials → Configure consent screen**
   - Set app name and email
   - Choose **External** audience
3. Go to **Clients → Create client**
   - Application type: `Web application`
   - Authorized JavaScript origins:
     ```
     http://localhost:5173
     ```
   - Authorized redirect URIs:
     ```
     http://localhost:5173/api/v1/auth/google/callback
     ```

4. Create a `.env` file:
```env
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-secret>
GOOGLE_REDIRECT_URI=<your-redirect-uri>
```

---

## Deploy (Railway + Vercel)

1. Deploy the frontend app to **Vercel**
2. Create **Postgres** and **backend app** in **Railway**
3. Configure domain DNS:
```
A       @    -> <Vercel app IP>
CNAME   www  -> cname.vercel-dns.com
CNAME   api  -> <Railway backend domain>
```

4. Update Google Console:
- Authorized JavaScript origin:
  ```
  https://example.com
  ```
- Authorized redirect URI:
  ```
  https://api.example.com/v1/auth/google/callback
  ```

5. Add an environment variable to **Vercel**:
```env
VITE_API_URL=https://api.example.com
```

6. Add environment variables to the **Railway FastAPI app**:
```env
# === App ===
ENVIRONMENT=production
PORT=8000
SECRET_KEY=generate_secret

# === Frontend / CORS ===
FRONTEND_URL=https://example.com
FRONTEND_OAUTH_ERROR_URL=https://example.com/oauth-error
CORS_ORIGINS=["https://example.com","https://www.example.com"]
COOKIE_DOMAIN=example.com

# === Google OAuth ===
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-secret>
GOOGLE_REDIRECT_URI=https://api.example.com/v1/auth/google/callback

# === PostgreSQL ===
POSTGRES_HOST=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}
POSTGRES_DB=${{Postgres.PGDATABASE}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
```

7. Enjoy 🚀

---

## Deployment notes

You can deploy this project to **any hosting provider**.

- The **frontend** does not require any changes
- For the **backend**:
  1. Remove the `railway.json` file
  2. Configure a pre-deploy (or release) step to run database migrations:
     ```bash
     uv run alembic upgrade head
     ```

Most platforms support a pre-deploy or release command
(e.g. Fly.io, Render, DigitalOcean, etc.).

## License
MIT
