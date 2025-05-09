from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings  # For file size limits

# Example: Define max upload size in settings.py (e.g., MAX_PDF_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024)
# If not set in settings, a default will be used here.


def validate_file_type(file):
    """Ensures the uploaded file is a PDF based on content type."""
    if file.content_type != 'application/pdf':
        # Consider using python-magic for more robust content type checking if needed
        raise ValidationError('Invalid file type. Only PDF files are allowed.')


def validate_file_size(file):
    """Ensures the uploaded file does not exceed a defined size limit."""
    # Get limit from settings or use a default (e.g., 5MB)
    max_size = getattr(settings, 'MAX_PDF_UPLOAD_SIZE_BYTES', 5 * 1024 * 1024)
    if file.size > max_size:
        raise ValidationError(
            f'File size cannot exceed {max_size // (1024*1024)}MB.')


class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(
        label='Upload PDF Bank Statement',
        validators=[validate_file_type, validate_file_size]
    )
    # We can add more fields later if needed, e.g., for output format preference
