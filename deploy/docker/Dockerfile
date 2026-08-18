FROM python:3.11.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --uid 65532 --create-home --home-dir /nonroot --shell /usr/sbin/nologin epik \
    && mkdir -p /app /artifacts \
    && chown -R 65532:65532 /app /artifacts

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src
COPY profiles /app/profiles
COPY schemas /app/schemas
COPY docs /app/docs

RUN pip install --no-cache-dir /app \
    && rm -rf /root/.cache/pip

USER 65532:65532
WORKDIR /artifacts
ENTRYPOINT ["epik"]
CMD ["--help"]
