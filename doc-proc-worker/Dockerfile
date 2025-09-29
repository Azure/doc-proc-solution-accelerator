# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy doc-proc-lib first (needed for requirements.txt)
COPY doc-proc-lib ./doc-proc-lib

# Create a temporary requirements.txt with corrected path
COPY doc-proc-worker/requirements.txt ./requirements-temp.txt
RUN sed 's|-e ../doc-proc-lib|-e ./doc-proc-lib|' requirements-temp.txt > requirements.txt && \
    rm requirements-temp.txt

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and run_worker.py
COPY doc-proc-worker/app ./app
COPY doc-proc-worker/run_worker.py ./

# Default port (keeping for compatibility, though worker may not use it)
# ENV PORT=8000
# EXPOSE 8000

# Run the worker
CMD ["python", "run_worker.py", "--pool"]
