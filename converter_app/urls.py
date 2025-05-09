from django.urls import path
from . import views

app_name = 'converter_app'  # Optional: for namespacing URLs

urlpatterns = [
    path('', views.upload_pdf_view, name='upload_pdf'),
    path('download/csv/', views.download_csv_view, name='download_csv'),
    path('download/excel/', views.download_excel_view, name='download_excel'),
    path('download/json/', views.download_json_view, name='download_json'),
    path('google-auth-redirect/', views.google_auth_redirect,
         name='google_auth_redirect'),
    path('oauth2callback/', views.google_auth_callback,
         name='google_auth_callback'),  # Matches redirect URI in GCP
    path('upload-to-sheets/', views.upload_to_google_sheets_view,
         name='upload_to_sheets'),
]
