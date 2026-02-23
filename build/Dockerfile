FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash inotify-tools coreutils curl jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
RUN uv python install 3.14.3 \
    && ln -sf $(uv python find 3.14) /usr/local/bin/python3 \
    && ln -sf $(uv python find 3.14) /usr/local/bin/python

COPY supervisor.sh /usr/local/bin/supervisor.sh
COPY default-loop.sh /usr/local/bin/default-loop.sh
RUN chmod +x /usr/local/bin/supervisor.sh

USER ubuntu
WORKDIR /daemon
ENTRYPOINT ["/usr/local/bin/supervisor.sh"]
