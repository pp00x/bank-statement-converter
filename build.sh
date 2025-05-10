#!/bin/bash

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput -v 3

echo "--- Listing contents of new STATIC_ROOT (static/) after collectstatic ---"
if [ -d "static/" ]; then
  ls -R static/
else
  echo "Directory static/ does NOT exist."
fi
echo "--- End of new STATIC_ROOT listing ---"

echo "--- Checking for critical static files in new location ---"
CRITICAL_STATIC_FILE="static/converter_app/script.js"
if [ -f "$CRITICAL_STATIC_FILE" ]; then
  echo "Found critical static file: $CRITICAL_STATIC_FILE"
else
  echo "ERROR: Critical static file NOT FOUND: $CRITICAL_STATIC_FILE"
  exit 1 # Cause the build to fail
fi
echo "--- End of critical static file check ---"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput