# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install deps into a local dir (easier to copy in next stage)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Run as non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY src/ ./src/

# Switch to non-root
USER appuser

EXPOSE 8000

# Use exec form (not shell form) so signals are handled correctly
# --reload only in dev; in prod override this via docker-compose command:
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
