FROM python:3.6-alpine

LABEL maintainer = "Felix Fennell <felnne@bas.ac.uk>"

ARG APP_PACKAGE_VERSION
ENV APP_PATH=/usr/src/app
ENV APP_VENV=/usr/local/virtualenvs/scar_add_metadata_toolbox
ENV PATH="$APP_VENV/bin:$PATH"
ENV FLASK_APP=scar_add_metadata_toolbox
ENV FLASK_ENV=production

WORKDIR $APP_PATH

RUN apk add --no-cache build-base libxslt-dev libffi-dev libressl-dev geos-dev proj-dev proj-util postgresql-dev
RUN python3 -m venv $APP_VENV

# Install application
COPY *.whl /tmp/wheelhouse/
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp36m/lxml-4.5.2-cp36-cp36m-linux_x86_64.whl
RUN python -m pip install http://bsl-repoa.nerc-bas.ac.uk/magic/v1/libraries/python/wheels/linux_x86_64/cp36m/pyproj-2.6.0-cp36-cp36m-linux_x86_64.whl
RUN python -m pip install --find-links=file:///tmp/wheelhouse $APP_PACKAGE_VERSION

# Patch CSW to workaround issues in PyCSW
COPY pycsw/patches/pycsw/plugins/profiles/apiso/apiso.py $APP_VENV/lib/python3.8/site-packages/pycsw/plugins/profiles/apiso/apiso.py

ENTRYPOINT ["flask"]
EXPOSE 5000
