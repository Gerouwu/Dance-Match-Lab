FROM python:3.10-slim

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/workspace/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libportaudio2 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev

COPY app/ ./app/

CMD ["tail", "-f", "/dev/null"]
