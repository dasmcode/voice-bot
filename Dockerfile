FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -sfS https://dotenvx.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
EXPOSE 8000
ENTRYPOINT ["dotenvx", "run", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
