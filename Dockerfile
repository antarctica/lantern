FROM python:3.6-alpine as base

LABEL maintainer = "Felix Fennell <felnne@bas.ac.uk>"

ENV APPPATH=/usr/src/app/
ENV PYTHONPATH=$APPPATH

RUN mkdir $APPPATH
WORKDIR $APPPATH

RUN apk add --no-cache libxslt-dev libffi-dev libressl-dev geos-dev proj-dev proj-util postgresql-dev


FROM base as build

ENV APPVENV=/usr/local/virtualenvs/scar_add_metadata_toolbox

RUN apk add --no-cache build-base
RUN python3 -m venv $APPVENV
ENV PATH="$APPVENV/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.1.0

COPY pyproject.toml poetry.toml poetry.lock $APPPATH
RUN poetry install --no-root --no-interaction --no-ansi


FROM base as run

ENV APPVENV=/usr/local/virtualenvs/scar_add_metadata_toolbox
ENV PATH="$APPVENV/bin:$PATH"
ENV FLASK_APP=scar_add_metadata_toolbox
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

COPY --from=build $APPVENV/ $APPVENV/
RUN mkdir -p /var/log/app/

ENTRYPOINT []
