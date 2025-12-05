FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

COPY . .

RUN chmod +x /app/api/scripts/aerich_init.sh /app/api/scripts/startup.sh

ENV ENVIRONMENT=${ENVIRONMENT}

EXPOSE 8000

CMD ["bash", "/app/api/scripts/startup.sh"]
