# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY app/ ./app/

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
