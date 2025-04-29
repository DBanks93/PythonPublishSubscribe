#!/bin/bash

#!/bin/bash

PUB_SUB_SERVICE_NAME=pubsub-emulator
PUB_SUB_HEALTH_URL=http://localhost:8085/v1/projects/test-project/topics

DATABASE_SERVICE_NAME=postgres-database
DATABASE_USER=appuser
DATABASE_HOST=localhost
DATABASE_PORT=5432

echo "Waiting for $PUB_SUB_SERVICE_NAME to be available..."
until curl --silent --fail $PUB_SUB_HEALTH_URL; do
  echo "$PUB_SUB_SERVICE_NAME is not healthy yet, trying again..."
  sleep 2
done
echo "$PUB_SUB_SERVICE_NAME is up and working."

echo "Waiting for $DATABASE_SERVICE_NAME to be available..."
until pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER; do
  echo "$DATABASE_SERVICE_NAME is not ready yet, trying again..."
  sleep 2
done
echo "$DATABASE_SERVICE_NAME is up and working."
