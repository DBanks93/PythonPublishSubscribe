#!/bin/bash

SERVICE_NAME=pubsub-emulator
HEALTH_URL=http://localhost:8085/v1/projects/your-project-id/topics

echo "Waiting for $SERVICE_NAME to be available"
until curl --silent --fail $HEALTH_URL; do
  echo "$SERVICE_NAME is not healthy yet, trying agin"
  sleep 2
done

echo "$SERVICE_NAME is up and working"