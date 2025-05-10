#!/bin/bash

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput -v 3

echo "--- Listing contents of STATIC_ROOT (staticfiles_build/static/) after collectstatic ---"
if [ -d "staticfiles_build/static/" ]; then
  ls -R staticfiles_build/static/
else
  echo "Directory staticfiles_build/static/ does NOT exist."
fi
echo "--- End of STATIC_ROOT listing ---"

echo "--- Checking for critical static files ---"
CRITICAL_STATIC_FILE="staticfiles_build/static/converter_app/script.js"
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