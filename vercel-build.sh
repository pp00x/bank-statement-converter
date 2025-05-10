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

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput