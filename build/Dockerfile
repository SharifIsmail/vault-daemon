FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash coreutils curl git jq ca-certificates gnupg \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 + Claude Code
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
RUN uv python install 3.14.3 \
    && ln -sf $(uv python find 3.14) /usr/local/bin/python3 \
    && ln -sf $(uv python find 3.14) /usr/local/bin/python

USER ubuntu
RUN curl -fsSL https://claude.ai/install.sh | bash
USER root
RUN cp -L /home/ubuntu/.local/bin/claude /usr/local/bin/claude

COPY supervisor.sh /usr/local/bin/supervisor.sh
COPY default-loop.sh /usr/local/bin/default-loop.sh
COPY default-readme.md /usr/local/bin/default-readme.md
RUN chmod +x /usr/local/bin/supervisor.sh

USER ubuntu
WORKDIR /daemon
ENTRYPOINT ["/usr/local/bin/supervisor.sh"]
