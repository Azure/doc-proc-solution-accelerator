# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy doc-proc-lib first (needed for requirements.txt)
COPY doc-proc-lib ./doc-proc-lib

WORKDIR /doc-proc-crawler

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*


COPY doc-proc-crawler/requirements.txt ./requirements.txt

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and run_crawler.py
COPY doc-proc-crawler/app ./app
COPY doc-proc-crawler/run_crawler.py ./

# Default port (keeping for compatibility, though crawler may not use it)
# ENV PORT=8000
# EXPOSE 8000

# Run the crawler
CMD ["python", "run_crawler.py"]
