[![Unit tests](https://github.com/ChameleonCloud/doni/actions/workflows/test.yml/badge.svg)](https://github.com/ChameleonCloud/doni/actions/workflows/test.yml)

# doni

Chameleon hardware registration and enrollment service

## Development

### Dependencies

  * [Poetry](https://getpoetry.org): `pip install poetry`
    > Note: this is not strictly necessary as most of the development can
      be accommodated solely via Docker. But, if you want to be running
      auto-formatting and using the local `black` lint rules, Poetry is
      used to install those.
  * [tox](https://tox.readthedocs.io/en/latest/): `pip install tox`
    > For running unit tests locally.
  * Docker, Docker Compose

### Installing dependencies for IDE (e.g. VSCode)

The `setup` target will just install all the project runtime and development
dependencies into a local virtualenv using Poetry. You can then configure the
IDE to point to the `.venv` directory created by Poetry as your Python
interpreter.

```shell
make setup
```

### Running a local development server

Run the `start` Make target to bring up a Docker Compose development
environment. The Flask application server should reload whenever any file is
changed.

```shell
make start
```

### Running unit tests

```shell
make test
```
