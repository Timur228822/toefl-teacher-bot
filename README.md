# 🎓 TOEFL Teacher Bot

AI-powered Telegram bot for TOEFL iBT preparation. Uses **Ollama** for local LLM inference, **PostgreSQL** for persistence, and **aiogram v3** for Telegram integration.

## Features

| Feature | Description |
|---------|-------------|
| 📝 **Diagnostics** | Quick diagnostic tests to assess your TOEFL level per skill |
| 📚 **Daily Practice** | AI-generated daily practice tasks across all 4 sections |
| 🎙 **Speaking** | Speaking prompts with voice-message evaluation |
| ✍️ **Writing** | Essay prompts with AI-powered scoring & feedback |
| 📊 **Stats** | Track your progress over time with per-skill breakdowns |
| ⚙️ **Settings** | Set proficiency level, daily goals, target score |

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Telegram    │────▶│  Bot (app)   │────▶│  PostgreSQL  │
│  Users       │◀────│  aiogram v3  │     │              │
└──────────────┘     │              │     └──────────────┘
                     │              │────▶┌──────────────┐
                     │              │     │   Ollama     │
                     └──────────────┘     │   LLM API   │
                                          └──────────────┘
```

## Quick Start — Local

### Prerequisites

- Python 3.11+
- PostgreSQL (local or remote)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 1. Clone & Configure

```bash
git clone <repo-url> && cd toefl-teacher
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=123456:YOUR_REAL_TOKEN_HERE
DATABASE_URL=postgresql://toefl:password@localhost:5432/toefl_teacher
```

> **Note:** If `DATABASE_URL` is set, it takes priority. Otherwise the bot falls back to individual `POSTGRES_*` variables.

### 2. Install & Run

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
python -m app.bot.main
```

### 3. (Optional) Docker Compose

If you prefer Docker for all three services:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3
docker compose logs -f app
```

## Deploy to Scalingo

The bot runs as a **worker** process (no HTTP port needed).

### 1. Create app & add PostgreSQL

```bash
scalingo create toefl-teacher
scalingo addons-add postgresql postgresql-sandbox
```

Scalingo automatically sets `DATABASE_URL` — the bot picks it up.

### 2. Set environment variables

```bash
scalingo env-set BOT_TOKEN=123456:YOUR_REAL_TOKEN_HERE
scalingo env-set OLLAMA_BASE_URL=http://your-ollama-host:11434
scalingo env-set OLLAMA_MODEL=llama3
```

### 3. Deploy

```bash
git push scalingo main
```

### 4. Scale the worker (not web)

```bash
scalingo scale worker:1
scalingo scale web:0
```

### 5. Check logs

```bash
scalingo logs -f
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | — | Telegram bot token |
| `DATABASE_URL` | — | — | Full database URL (Scalingo sets this automatically). If set, overrides all `POSTGRES_*` vars |
| `POSTGRES_HOST` | — | `localhost` | PostgreSQL host (used only if `DATABASE_URL` is not set) |
| `POSTGRES_PORT` | — | `5432` | PostgreSQL port |
| `POSTGRES_USER` | — | `toefl` | DB username |
| `POSTGRES_PASSWORD` | — | `changeme` | DB password |
| `POSTGRES_DB` | — | `toefl_teacher` | DB name |
| `OLLAMA_BASE_URL` | — | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | — | `llama3` | Default LLM model |
| `LOG_LEVEL` | — | `INFO` | Logging level |
| `ADMIN_IDS` | — | `[]` | JSON array of admin Telegram IDs |

> **DATABASE_URL format:** Scalingo provides `postgres://user:pass@host:port/db`. The bot automatically converts `postgres://` → `postgresql+asyncpg://` for SQLAlchemy.

## Project Structure

```
.
├── Dockerfile
├── docker-compose.yml
├── Procfile                     # Scalingo worker entry point
├── requirements.txt
├── .env.example
├── .gitignore                   # .env and .venv are excluded
├── README.md
└── app/
    ├── bot/
    │   ├── main.py              # Entry point: bot init, polling
    │   ├── keyboards.py         # Inline keyboard factories
    │   └── handlers/
    │       ├── start.py         # /start + main menu
    │       ├── diagnostics.py   # Diagnostic tests
    │       ├── daily_practice.py
    │       ├── speaking.py
    │       ├── writing.py
    │       ├── stats.py         # User statistics
    │       └── settings.py      # User preferences
    ├── core/
    │   └── config.py            # Pydantic settings (DATABASE_URL support)
    ├── db/
    │   ├── session.py           # Async engine & session
    │   ├── models.py            # SQLAlchemy ORM models
    │   └── crud.py              # CRUD helpers
    └── services/
        └── ollama.py            # Ollama HTTP client
```

## Important

- **Never commit `.env`** — it contains secrets. Use `.env.example` as a template.
- **Never commit `.venv/`** — it's in `.gitignore`.
- Tables are auto-created on startup. For production migrations, use Alembic.

## License

MIT
