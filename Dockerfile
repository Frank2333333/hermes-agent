FROM debian:13.4

# Disable Python stdout buffering to ensure logs are printed immediately
ENV PYTHONUNBUFFERED=1

# Default to fast mainland mirrors; use HTTP during bootstrap to avoid
# certificate issues before ca-certificates is installed.
ARG DEBIAN_MIRROR=http://mirrors.tuna.tsinghua.edu.cn/debian
ARG DEBIAN_SECURITY_MIRROR=http://mirrors.tuna.tsinghua.edu.cn/debian-security
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
# Install system dependencies in one layer, clear APT cache
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|URIs: http://deb.debian.org/debian|URIs: ${DEBIAN_MIRROR}|g" /etc/apt/sources.list.d/debian.sources && \
        sed -i "s|URIs: http://deb.debian.org/debian-security|URIs: ${DEBIAN_SECURITY_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi && \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" /etc/apt/sources.list && \
        sed -i "s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" /etc/apt/sources.list; \
    fi && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates build-essential python3 python3-dev python3-pip python3-venv ripgrep gcc libffi-dev procps git gosu && \
    rm -rf /var/lib/apt/lists/*

# Non-root user for runtime; UID can be overridden via HERMES_UID at runtime
RUN useradd -u 10000 -m -d /opt/data hermes

WORKDIR /opt/hermes

# ---------- Source code ----------
COPY --chown=hermes:hermes . .

# ---------- Python virtualenv ----------
RUN chown hermes:hermes /opt/hermes && \
    chmod 0755 /opt/hermes/docker/entrypoint.sh
USER hermes
RUN python3 -m venv /opt/hermes/.venv && \
    /opt/hermes/.venv/bin/pip install --no-cache-dir --index-url ${PIP_INDEX_URL} --trusted-host ${PIP_TRUSTED_HOST} --upgrade pip setuptools wheel && \
    /opt/hermes/.venv/bin/pip install --no-cache-dir --index-url ${PIP_INDEX_URL} --trusted-host ${PIP_TRUSTED_HOST} -e . && \
    /opt/hermes/.venv/bin/pip install --no-cache-dir --index-url ${PIP_INDEX_URL} --trusted-host ${PIP_TRUSTED_HOST} "aiohttp>=3.13.3,<4" "croniter>=6.0.0,<7" "ptyprocess>=0.7.0,<1"

# ---------- Runtime ----------
USER root
ENV HERMES_HOME=/opt/data
VOLUME [ "/opt/data" ]
ENTRYPOINT [ "/opt/hermes/docker/entrypoint.sh" ]
