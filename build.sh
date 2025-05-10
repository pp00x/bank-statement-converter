#!/bin/bash

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Build script completed."