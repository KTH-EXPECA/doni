ARG python_version=3.8

FROM python:${python_version} as builder

# netifaces doesn't have wheels built for Python >3.6; build it ourselves
# and then install in the next stage.
# yappi also doesn't have any wheel built.
RUN pip wheel netifaces --wheel-dir /custom-wheels \
  https://github.com/al45tair/netifaces/archive/release_0_10_9.tar.gz \
  https://files.pythonhosted.org/packages/4c/18/1b9387c7d3bf0d7aa54773ded7d286bcb8b04ec242404969f6656a385a11/yappi-1.3.2.tar.gz

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
  .wheels/netifaces-0.10.9-cp38-cp38-linux_x86_64.whl \
  .wheels/yappi-1.3.2-cp38-cp38-linux_x86_64.whl

RUN poetry install --no-dev

ADD docker/start_server.sh .
ADD doni ./doni

EXPOSE 8001
CMD [ "./start_server.sh" ]
