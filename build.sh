#!/bin/bash
# This script is intended to be run by @vercel/static-build

echo "BUILD.SH (for @vercel/static-build): Installing dependencies for collectstatic..."
# Try to ensure pip for python3 is used. This might need adjustment based on Vercel's static-build env.
python3 -m pip install -r requirements.txt

echo "BUILD.SH: Collecting static files into 'static' directory..." # Updated directory name
python3 manage.py collectstatic --noinput

echo "BUILD.SH: Listing contents of STATIC_ROOT (static/)..." # Updated directory name
if [ -d "static/" ]; then # Updated directory name
  ls -R static/ # Updated directory name
  echo "BUILD.SH: Critical file static/converter_app/script.js check:" # Updated directory name
  if [ -f "static/converter_app/script.js" ]; then # Updated directory name
    echo "BUILD.SH: Found critical static file: static/converter_app/script.js" # Updated directory name
  else
    echo "BUILD.SH: ERROR: Critical static file NOT FOUND: static/converter_app/script.js" # Updated directory name
    # Consider exiting with 1 if this is critical for the build to succeed
  fi
else
  echo "BUILD.SH: Directory static/ does NOT exist after collectstatic." # Updated directory name
  # Consider exiting with 1
fi
echo "BUILD.SH: Static files collection process finished."