# This should match the default Python version in the test actions
ARG python_version=3.8

FROM python:${python_version} as builder
# netifaces doesn't have wheels built for Python >3.6; build it ourselves
# and then install in the next stage.
# yappi also doesn't have any wheel built.
# Added wheel for psutil to make ARM64 happy

RUN pip wheel \
  --wheel-dir /custom-wheels \
  netifaces \
  yappi \
  psutil \
  typed-ast

FROM python:${python_version}-slim as base

RUN mkdir -p /work
WORKDIR /work

RUN pip3 install poetry
RUN poetry config virtualenvs.create false --local

COPY --from=builder /custom-wheels .wheels

ADD poetry.lock .
ADD pyproject.toml .

# NOTE: if the Python version changes, this will need to be renamed to match
# the CPython version it was built for.
# This is not hard-coded in the pyproject.toml so that poetry can still
# be used on the host machine, which won't have this .wheels directory.
RUN poetry add \
  .wheels/*

ADD doni ./doni

RUN poetry install --no-dev

EXPOSE 8001
CMD [ "doni-api" ]
