# Guide: Successfully Serving Django Static Files on Vercel

This document summarizes the key configuration steps that resolved issues with serving Django static files (like CSS, JavaScript, images) on the Vercel platform. The primary problem was 404 errors for static assets, despite them being collected during the build.

## Core Principle

The solution leverages Vercel's default behavior for serving static files. Vercel automatically serves content from a directory named `static` (or `public`) located at the root of your project if that directory is designated as a build output (`distDir`). By ensuring our Django `collectstatic` process outputs to a root `static` directory, and by configuring Vercel to recognize this, we allow Vercel's efficient edge network to handle static file requests directly.

## Key Configuration Steps

The successful setup involves specific configurations in `settings.py`, `build.sh`, and `vercel.json`.

### 1. Django `settings.py` (`config/settings.py`)

*   **`STATIC_URL`**: Defines the URL prefix for static files. This should typically be `/static/`.
    ```python
    STATIC_URL = '/static/'
    ```

*   **`STATIC_ROOT`**: This is the absolute filesystem path where `manage.py collectstatic` will gather all static files. For Vercel's default serving to work, this should point to a directory named `static` at the root of your project.
    ```python
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent # Or your project's base directory

    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    ```

*   **`STATICFILES_DIRS`**: This lists additional directories Django should look for static files in (besides app-specific `static` subdirectories). If your project's static files are primarily within your apps (e.g., `your_app/static/your_app/somefile.js`), this can often be left empty.
    ```python
    STATICFILES_DIRS = [] # If using app-namespaced static files primarily
    # Or, if you have a project-level static folder:
    # STATICFILES_DIRS = [os.path.join(BASE_DIR, 'project_wide_static_files')]
    ```

*   **Whitenoise Configuration (Recommended Best Practice)**: While Vercel will serve the files, configuring Whitenoise is good for consistency and as a fallback.
    *   Add to `MIDDLEWARE` (place it after `SecurityMiddleware`):
        ```python
        MIDDLEWARE = [
            'django.middleware.security.SecurityMiddleware',
            'whitenoise.middleware.WhiteNoiseMiddleware',
            # ... other middleware ...
        ]
        ```
    *   Set `STATICFILES_STORAGE` for compression and manifest (cache-busting):
        ```python
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ```

### 2. `build.sh` (for Vercel's `@vercel/static-build` step)

This script is responsible for preparing your static assets. It runs in a separate build environment on Vercel.

*   **Install Dependencies**: It must install Python dependencies required for `collectstatic` (like Django itself).
*   **Run `collectstatic`**: Execute Django's command to gather static files into `STATIC_ROOT` (which is now the `static` directory at the project root).

```bash
#!/bin/bash

echo "BUILD.SH: Installing dependencies for collectstatic..."
# Ensure pip for python3 is used. Vercel's @vercel/static-build environment should provide python3.
python3 -m pip install -r requirements.txt

echo "BUILD.SH: Collecting static files into 'static' directory..."
python3 manage.py collectstatic --noinput 

echo "BUILD.SH: Static files collection process finished."
# Optional: Add 'ls -R static/' here for debugging build logs
```

### 3. `vercel.json` (Vercel Project Configuration)

This file defines how Vercel builds and routes your project.

*   **Two Build Steps**:
    1.  `@vercel/python`: For your main Django WSGI application.
    2.  `@vercel/static-build`: To run `build.sh` and handle static assets.
*   **`distDir`**: For the `@vercel/static-build` step, `distDir` must be set to `"static"` (matching your `STATIC_ROOT` directory name). This tells Vercel where the output of this build step is.
*   **Routes**:
    *   **No explicit route for `/static/(.*)` is needed.** Vercel will automatically serve files from the `distDir` ("static") if the URL matches the file structure within it (e.g., a request to `/static/converter_app/script.js` will be served from the `static/converter_app/script.js` file in your `distDir`).
    *   Include a catch-all route for your Django application.

```json
{
  "version": 2,
  "builds": [
    {
      "src": "config/wsgi.py", // Path to your project's wsgi.py
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb", "runtime": "python3.13" } // Adjust runtime as needed
    },
    {
      "src": "build.sh",
      "use": "@vercel/static-build",
      "config": { "distDir": "static" } // Output of build.sh is the 'static' directory
    }
  ],
  "routes": [
    // No explicit /static/... route needed here if Vercel's default serving works
    {
      "src": "/(.*)", // Catch-all for Django application
      "dest": "config/wsgi.py" // Path to your project's wsgi.py
    }
  ]
}
```

## Why This Configuration Works

1.  **`collectstatic`**: The `build.sh` script (executed by `@vercel/static-build`) runs `manage.py collectstatic`. Since `STATIC_ROOT` is set to `your_project_root/static`, all static files (from apps and `STATICFILES_DIRS`) are copied into this `static` directory.
2.  **`distDir`**: In `vercel.json`, `distDir: "static"` tells Vercel that the `static` directory (created by `build.sh`) is the output of the static asset build.
3.  **Vercel's Default Serving**: Vercel's platform has a built-in mechanism to serve files from a directory named `static` (or `public`) if it's at the project root and recognized as a build output (via `distDir`). When a browser requests a URL like `/static/converter_app/script.js`, Vercel's edge network directly serves the file `converter_app/script.js` from the `static` (distDir) directory.
4.  **No Route Conflict**: By removing explicit `/static/(.*)` routes from `vercel.json`, we allow Vercel's default static serving to handle these requests without interference. The Django application (and Whitenoise) will only receive requests that Vercel doesn't serve directly (e.g., your actual application URLs).

This setup ensures that static files are handled by Vercel's optimized CDN, leading to better performance, while Django handles the dynamic parts of your application. Whitenoise remains a good addition for ensuring Django *could* serve static files if needed (e.g., in development with `runserver --nostatic` or if a static request somehow bypassed Vercel's edge).