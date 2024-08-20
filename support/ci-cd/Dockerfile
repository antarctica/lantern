FROM python:3.9-alpine AS base

LABEL maintainer="Felix Fennell <felnne@bas.ac.uk>"

RUN apk add --no-cache \
    libxslt-dev \
    libffi-dev \
    openssl-dev \
    libxml2-utils \
    geos-dev \
    proj-dev \
    proj-util \
    postgresql-dev \
    cargo

FROM base AS build

RUN apk add --no-cache build-base cargo
RUN python3 -m pip install pipx
RUN python3 -m pipx install poetry==1.8.2

ENV PATH="/root/.local/bin:$PATH"
COPY pyproject.toml poetry.lock /
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-root --no-interaction --no-ansi
RUN poetry run python -m pip install --upgrade pip

FROM base AS run

COPY --from=build /root/.local/share/pipx/venvs/poetry /root/.local/share/pipx/venvs/poetry
COPY --from=build /root/.local/bin/poetry /root/.local/bin/poetry
COPY --from=build /.venv/ /.venv
ENV PATH="/venv/bin:/root/.local/bin:$PATH"
RUN poetry config virtualenvs.in-project true
ENTRYPOINT []
