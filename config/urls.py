"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include  # Added include
from django.conf import settings  # Added
from django.conf.urls.static import static  # Added

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('converter_app.urls')),  # Added this line for our app
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    # Note: STATIC_ROOT is typically only used for production collectstatic.
    # For development, Django's staticfiles app usually finds files in app 'static' dirs.
    # However, explicitly adding this can sometimes help, but ensure STATIC_URL is set in settings.py (it is by default).
    # A more common pattern for dev might not need this if 'django.contrib.staticfiles' is in INSTALLED_APPS
    # and the runserver command handles it automatically. Let's keep it simple for now.
    # If static files don't load, we might need to configure STATICFILES_DIRS in settings.py.
