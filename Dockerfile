# ── Stage 1: builder ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="TOEFL Teacher Bot"

# Non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN chown -R botuser:botuser /app

USER botuser

CMD ["python", "-m", "app.bot.main"]
