ARG python_version=3.8
FROM python:${python_version}-slim

RUN mkdir -p /work
WORKDIR /work

RUN pip3 install poetry
RUN poetry config virtualenvs.create false --local

ADD poetry.lock .
ADD pyproject.toml .
RUN poetry install --no-dev

ADD docker/start_server.sh .
ADD doni ./doni

EXPOSE 8001
CMD [ "./start_server.sh" ]
