FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8001/health/ || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
