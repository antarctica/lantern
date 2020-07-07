FROM python:3.8-alpine

LABEL maintainer = "Felix Fennell <felnne@bas.ac.uk>"

ARG APP_PACKAGE_VERSION
ENV APP_PATH=/usr/src/app
ENV APP_VENV=/usr/local/virtualenvs/scar_add_metadata_toolbox
WORKDIR $APP_PATH

RUN apk add --no-cache build-base libxslt-dev libffi-dev libressl-dev git geos-dev proj-dev proj-util postgresql-dev

RUN python3 -m venv $APP_VENV

ENV PATH="$APP_VENV/bin:$PATH"
ENV FLASK_APP=/usr/src/app/entrypoint.py
ENV FLASK_ENV=production

## Pre-install wheels to save time
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp38m/lxml-4.5.0-cp38-cp38-linux_x86_64.whl
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp38m/pyproj-2.6.0-cp38-cp38-linux_x86_64.whl

# Pre-install pre-release wheels (temporary)
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/projects/metadata-library/latest/dist/bas_metadata_library-0.0.0-py3-none-any.whl

# Install application
COPY entrypoint.py /usr/src/app/
COPY *.whl /tmp/wheelhouse/
RUN python -m pip install --find-links=file:///tmp/wheelhouse $APP_PACKAGE_VERSION

# Patch CSW to workaround issues in PyCSW
COPY pycsw/patches/pycsw/plugins/profiles/apiso/apiso.py $APP_VENV/lib/python3.8/site-packages/pycsw/plugins/profiles/apiso/apiso.py

ENTRYPOINT ["flask"]
EXPOSE 5000
