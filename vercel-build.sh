#!/bin/bash

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput -v 3

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput