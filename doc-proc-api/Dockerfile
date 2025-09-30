# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy doc-proc-lib first (needed for editable install)
COPY doc-proc-lib /doc-proc-lib

WORKDIR /doc-proc-api

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# # Create a temporary requirements.txt with corrected path
# COPY doc-proc-api/requirements.txt ./requirements-temp.txt
# RUN sed 's|-e ../doc-proc-lib|-e /doc-proc-lib|' requirements-temp.txt > requirements.txt && \
#     rm requirements-temp.txt

COPY doc-proc-api/requirements.txt ./requirements.txt

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY doc-proc-api/app ./app
COPY doc-proc-api/main.py ./main.py

# Default port
ENV PORT=8090
EXPOSE 8090

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
