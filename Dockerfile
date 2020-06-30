FROM python:3.8-alpine as base

LABEL maintainer = "Felix Fennell <felnne@bas.ac.uk>"

ENV APPPATH=/usr/src/app/
ENV PYTHONPATH=$APPPATH

RUN mkdir $APPPATH
WORKDIR $APPPATH

RUN apk add --no-cache libxslt-dev libffi-dev libressl-dev git geos-dev proj-dev proj-util postgresql-dev


FROM base as build

ENV APPVENV=/usr/local/virtualenvs/scar_add_metadata_toolbox

RUN apk add --no-cache build-base
RUN python3 -m venv $APPVENV
ENV PATH="$APPVENV/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.0.0

## pre-install wheels to save time (this can be disabled if you can't access `bsl-repoa`)
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp38m/lxml-4.5.0-cp38-cp38-linux_x86_64.whl
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp38m/pyproj-2.6.0-cp38-cp38-linux_x86_64.whl

# pre-install pre-release wheels (temporary)
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/projects/metadata-library/latest/dist/bas_metadata_library-0.0.0-py3-none-any.whl

COPY pyproject.toml poetry.toml poetry.lock $APPPATH
RUN poetry update --no-interaction --no-ansi
RUN poetry install --no-root --no-interaction --no-ansi

# Patch CSW to workaround issues in PyCSW
COPY ./support/pycsw/patches/pycsw/plugins/profiles/apiso/apiso.py $APPVENV/lib/python3.8/site-packages/pycsw/plugins/profiles/apiso/apiso.py


FROM base as run

ENV APPVENV=/usr/local/virtualenvs/scar_add_metadata_toolbox
ENV PATH="$APPVENV/bin:$PATH"
ENV FLASK_APP=/usr/src/app/manage.py
ENV FLASK_ENV=development

COPY --from=build $APPVENV/ $APPVENV/
RUN mkdir -p /var/log/app/

ENTRYPOINT []
