#!/bin/sh

if [ "$WAIT_FOR_DB" = "true" ]; then
  echo "Waiting for MySQL..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
  echo "MySQL is up!"
fi

exec "$@"
