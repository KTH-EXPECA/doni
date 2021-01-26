# doni

Chameleon hardware registration and enrollment service

## Development

### Dependencies

  * [Poetry](https://getpoetry.org): `pip install poetry`
    > Note: this is not strictly necessary as most of the development can
      be accommodated solely via Docker. But, if you want to be running
      auto-formatting and using the local `black` lint rules, Poetry is
      used to install those.
  * Docker, Docker Compose

### Running a local development server

Run the `start` Make target to bring up a Docker Compose development
environment. The Flask application server should reload whenever any file is
changed.

```shell
make start
```
