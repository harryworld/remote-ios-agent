FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/remote-ios-agent
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir uv==0.9.7 \
    && UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --frozen --extra device --extra mcp --no-dev --no-editable \
    && useradd --create-home --uid 10001 agent
ENV PATH="/opt/venv/bin:$PATH"
USER agent
WORKDIR /home/agent
ENTRYPOINT ["remote-ios"]
CMD ["doctor"]
