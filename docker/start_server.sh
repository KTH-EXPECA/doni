#!/usr/bin/env bash
exec gunicorn "doni:create_app()" -b 0.0.0.0:${PORT:-8001} \
  --access-logfile - \
  --error-logfile - \
  --capture-output --enable-stdio-inheritance \
  ${GUNICORN_ARGS[@]:-}
