FROM python:3.12-slim

# Install LaTeX and required packages
RUN apt-get update && apt-get install -y \
    texlive \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . .

CMD ["/app/.venv/bin/fastapi", "run", "src/main.py", "--port", "80", "--host", "0.0.0.0", "--proxy-headers"]