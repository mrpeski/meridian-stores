FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src

RUN pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENV MERIDIAN_STORES_API_HOST=0.0.0.0
ENV MERIDIAN_STORES_API_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn hello_world.app:app --host \"${MERIDIAN_STORES_API_HOST}\" --port \"${MERIDIAN_STORES_API_PORT}\""]
