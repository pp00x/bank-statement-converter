#!/bin/bash
# This script is intended to be run by @vercel/static-build

echo "BUILD.SH (for @vercel/static-build): Installing dependencies for collectstatic..."
# Try to ensure pip for python3 is used. This might need adjustment based on Vercel's static-build env.
python3 -m pip install -r requirements.txt

echo "BUILD.SH: Collecting static files into 'staticfiles' directory..."
python3 manage.py collectstatic --noinput 

echo "BUILD.SH: Listing contents of STATIC_ROOT (staticfiles/)..."
if [ -d "staticfiles/" ]; then
  ls -R staticfiles/
  echo "BUILD.SH: Critical file staticfiles/converter_app/script.js check:"
  if [ -f "staticfiles/converter_app/script.js" ]; then
    echo "BUILD.SH: Found critical static file: staticfiles/converter_app/script.js"
  else
    echo "BUILD.SH: ERROR: Critical static file NOT FOUND: staticfiles/converter_app/script.js"
    # Consider exiting with 1 if this is critical for the build to succeed
  fi
else
  echo "BUILD.SH: Directory staticfiles/ does NOT exist after collectstatic."
  # Consider exiting with 1
fi
echo "BUILD.SH: Static files collection process finished."