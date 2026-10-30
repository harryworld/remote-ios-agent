FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/remote-ios-agent
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir '.[device,mcp]' && useradd --create-home --uid 10001 agent
USER agent
WORKDIR /home/agent
ENTRYPOINT ["remote-ios"]
CMD ["doctor"]
