FROM python:3.8-alpine as base

LABEL maintainer = "Felix Fennell <felnne@bas.ac.uk>"

ENV APPPATH=/usr/src/app/
ENV PYTHONPATH=$APPPATH

RUN mkdir $APPPATH
WORKDIR $APPPATH

RUN apk add --no-cache libxslt-dev libffi-dev libressl-dev git


FROM base as build

ENV APPVENV=/usr/local/virtualenvs/bas_add_metadata_toolbox

RUN apk add --no-cache build-base
RUN python3 -m venv $APPVENV
ENV PATH="$APPVENV/bin:$PATH"

## pre-install known wheels to save time
# ADD http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp38m/lxml-4.5.0-cp38-cp38-linux_x86_64.whl /tmp/wheelhouse/
# RUN pip install --no-index --find-links=file:///tmp/wheelhouse lxml==4.5.0

# pre-install pre-release wheels
COPY support/python-packages/bas_metadata_library-0.0.0-py3-none-any.whl /tmp/wheelhouse/
RUN pip install --find-links=file:///tmp/wheelhouse bas-metadata-library==0.0.0

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.0.0

# COPY pyproject.toml poetry.toml poetry.lock $APPPATH
COPY pyproject.toml poetry.toml $APPPATH
RUN poetry update --no-interaction --no-ansi
RUN poetry install --no-root --no-interaction --no-ansi


FROM base as run

ENV APPVENV=/usr/local/virtualenvs/bas_add_metadata_toolbox
ENV PATH="$APPVENV/bin:$PATH"

COPY --from=build $APPVENV/ $APPVENV/

ENTRYPOINT []
