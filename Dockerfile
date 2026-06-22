# syntax=docker/dockerfile:1
# Container image for the tablebridge MCP server.
#
# The server speaks MCP (JSON-RPC) over stdio. Mount the folder of data files
# you want to query at /data (read-only is fine) and run interactively (-i):
#
#   docker build -t tablebridge .
#   docker run --rm -i -v /path/to/your/data:/data:ro tablebridge
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TABLEBRIDGE_DATA_DIR=/data

WORKDIR /app
COPY . /app
RUN pip install . \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /data && chown app /data

USER app
VOLUME ["/data"]

ENTRYPOINT ["tablebridge"]
