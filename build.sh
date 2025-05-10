#!/bin/bash

echo "BUILD.SH: Installing dependencies..."
pip install -r requirements.txt

echo "BUILD.SH: Collecting static files into 'staticfiles' directory..."
python3 manage.py collectstatic --noinput # Using python3 as in article

echo "BUILD.SH: Listing contents of STATIC_ROOT (staticfiles/)..."
if [ -d "staticfiles/" ]; then
  ls -R staticfiles/
else
  echo "BUILD.SH: Directory staticfiles/ does NOT exist after collectstatic."
  exit 1 # Fail build if collectstatic didn't create the dir
fi
echo "BUILD.SH: Static files collected and listed."

# Migrations are usually handled by the main Python runtime build or manually,
# not typically in the static build script if it's separate.
# For now, let's keep migrations out of this specific build.sh
# which is intended for @vercel/static-build.
# If migrations are needed, they should be in a script run by @vercel/python
# or handled post-deployment.
# The article's build.sh does not include migrations.