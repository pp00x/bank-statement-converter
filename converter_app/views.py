from django.http import HttpResponse, Http404
import google.auth.transport.requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.urls import reverse
from django.shortcuts import redirect
import json  # Re-importing here for clarity, though already imported above
from .utils import convert_data_to_csv_string, convert_data_to_excel_bytes
from django.shortcuts import render, redirect  # Added redirect
from django.http import JsonResponse  # Added JsonResponse
from django.conf import settings
import google.generativeai as genai
import json  # For parsing JSON response if needed, and for displaying
from datetime import datetime  # Added for date parsing
import tempfile  # Added
import os  # Added
from django.core.files.uploadedfile import InMemoryUploadedFile  # Added
from .forms import PDFUploadForm
from .models import StatementData  # Added import for the new model
import logging  # Added for logging

# Instantiate logger
logger = logging.getLogger(__name__)


# Create your views here.
def upload_pdf_view(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.debug(f"Enter upload_pdf_view. Method: {request.method}", extra={
                 'request_id': request_id, 'method': request.method, 'path': request.path})
    # This view now handles both the initial GET request (rendering the page)
    # and the AJAX POST request (processing the file).

    if request.method == 'POST':
        logger.info("upload_pdf_view: POST request received.",
                    extra={'request_id': request_id})
        # --- AJAX POST Request Handling ---
        # Check if it's an AJAX request (optional but good practice)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            logger.warning("upload_pdf_view: Non-AJAX POST request received.",
                           extra={'request_id': request_id})
            return JsonResponse({'status': 'error', 'message': 'Invalid request type.'}, status=400)

        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']
            logger.info(f"upload_pdf_view: Form is valid. Processing PDF: {pdf_file.name}",
                        extra={'request_id': request_id, 'pdf_filename': pdf_file.name, 'size_bytes': pdf_file.size})

            # Clear all session data related to any PREVIOUS PDF processing cycle
            # before starting a new one. Google credentials should persist.
            logger.info("upload_pdf_view: New PDF upload. Clearing session data from any previous PDF processing cycle.", extra={
                        'request_id': request_id})
            keys_to_clear = [
                'statement_data_id',        # ID of the previously processed statement
                'date_range_string',        # Date range of the previously processed statement
                'gsheet_success_message',   # Success message from a previous GSheet upload
                'gsheet_url',               # URL from a previous GSheet upload
                'gsheet_title',             # Title from a previous GSheet upload
                'upload_message',           # General upload message from previous operations
                'user_message',             # General user message from previous operations
                'error_message'             # General error message from previous operations
            ]
            for key in keys_to_clear:
                if key in request.session:
                    logger.debug(f"Clearing '{key}' from session: {request.session.get(key)}", extra={
                                 'request_id': request_id})
                    request.session.pop(key, None)

            # Ensure 'statement_data' (old key, if present from very old sessions) is also cleared
            if 'statement_data' in request.session:
                logger.debug(f"Clearing legacy 'statement_data' key from session.", extra={
                             'request_id': request_id})
                request.session.pop('statement_data', None)

            try:
                logger.debug("upload_pdf_view: Configuring Gemini API for new PDF.", extra={
                             'request_id': request_id})
                genai.configure(api_key=settings.GEMINI_API_KEY)

                file_path_for_api = None
                temp_file_created = False
                uploaded_file_part = None  # Initialize to ensure it's defined for finally

                try:
                    if isinstance(pdf_file, InMemoryUploadedFile):
                        logger.debug("upload_pdf_view: Handling InMemoryUploadedFile.", extra={
                                     'request_id': request_id})
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            for chunk in pdf_file.chunks():
                                tmp_file.write(chunk)
                            file_path_for_api = tmp_file.name
                            temp_file_created = True
                        logger.debug(f"upload_pdf_view: Temp file created for InMemoryUploadedFile: {file_path_for_api}",
                                     extra={'request_id': request_id, 'temp_file_path': file_path_for_api})
                    else:
                        file_path_for_api = pdf_file.temporary_file_path()
                        logger.debug(f"upload_pdf_view: Using Django's temporary_file_path: {file_path_for_api}",
                                     extra={'request_id': request_id, 'temp_file_path': file_path_for_api})

                    if not file_path_for_api:
                        logger.error("upload_pdf_view: Could not determine file path for API.", extra={
                                     'request_id': request_id})
                        raise ValueError(
                            "Could not determine file path for API.")

                    logger.info(f"upload_pdf_view: Uploading file to Gemini: {pdf_file.name}",
                                extra={'request_id': request_id, 'pdf_filename': pdf_file.name, 'api_file_path': file_path_for_api})
                    uploaded_file_part = genai.upload_file(
                        path=file_path_for_api,
                        display_name=pdf_file.name
                    )
                    logger.info(f"upload_pdf_view: File uploaded to Gemini successfully. Gemini File ID: {uploaded_file_part.name}",
                                extra={'request_id': request_id, 'gemini_file_id': uploaded_file_part.name})

                    model = genai.GenerativeModel(
                        model_name=settings.GEMINI_MODEL_NAME)
                    logger.info(f"upload_pdf_view: Calling Gemini model '{settings.GEMINI_MODEL_NAME}' for analysis.",
                                extra={'request_id': request_id, 'model_name': settings.GEMINI_MODEL_NAME})
                    prompt = f"""
                    Please analyze the content of the provided PDF bank statement.
                    Extract all transaction details.
                    Return the data as a JSON object.
                    The JSON object should be a list of transactions.
                    Each transaction object in the list should have the following keys:
                    - "date": (string, e.g., "YYYY-MM-DD" or "DD/MM/YYYY")
                    - "description": (string)
                    - "debit": (float or null, if no debit amount)
                    - "credit": (float or null, if no credit amount)
                    - "balance": (float, the balance after the transaction)

                    If the document does not appear to be a bank statement or if no transactions can be reliably extracted,
                    please return a JSON object with a single key "error", like this:
                    {{ "error": "Document does not appear to be a bank statement or no transactions found." }}

                    Ensure the output contains ONLY the JSON object. Do NOT wrap the JSON in markdown code fences (like ```json ... ```).
                    The response should start directly with `{{` or `[` and end with `}}` or `]`.
                    Example of a single transaction object if successful:
                    {{
                        "date": "2024-01-15",
                        "description": "Grocery Store Purchase",
                        "debit": 55.75,
                        "credit": null,
                        "balance": 1234.50
                    }}
                    """
                    response = model.generate_content(
                        [uploaded_file_part, prompt])
                    raw_response_text = response.text
                    logger.debug(f"upload_pdf_view: Gemini raw response received. Length: {len(raw_response_text)}",
                                 extra={'request_id': request_id, 'response_length': len(raw_response_text)})

                    # Attempt to strip markdown fences if present
                    cleaned_response_text = raw_response_text.strip()
                    if cleaned_response_text.startswith("```json"):
                        # Remove ```json
                        cleaned_response_text = cleaned_response_text[7:]
                    # General markdown fence
                    if cleaned_response_text.startswith("```"):
                        cleaned_response_text = cleaned_response_text[3:]
                    if cleaned_response_text.endswith("```"):
                        cleaned_response_text = cleaned_response_text[:-3]
                    cleaned_response_text = cleaned_response_text.strip()  # Strip again after removal

                    try:
                        parsed_data = json.loads(cleaned_response_text)
                        logger.debug("upload_pdf_view: Gemini response parsed as JSON.", extra={
                                     'request_id': request_id})
                        if isinstance(parsed_data, dict) and "error" in parsed_data:
                            logger.warning(f"upload_pdf_view: Gemini API returned structured error: {parsed_data['error']}",
                                           extra={'request_id': request_id, 'gemini_error': parsed_data['error']})
                            return JsonResponse({'status': 'error', 'message': f"Could not process PDF: {parsed_data['error']}"}, status=400)
                        elif isinstance(parsed_data, list):
                            if not parsed_data:  # Empty list of transactions
                                logger.info("upload_pdf_view: No transactions found in PDF by Gemini.", extra={
                                            'request_id': request_id})
                                return JsonResponse({'status': 'success', 'message': "No transactions found in the PDF. It might not be a bank statement or it's empty.", 'results_ready': False})
                            else:
                                logger.info(f"upload_pdf_view: Successfully extracted {len(parsed_data)} transactions by Gemini.",
                                            extra={'request_id': request_id, 'transaction_count': len(parsed_data)})
                                parsed_json_data = parsed_data  # Keep local var for processing
                                user_friendly_message = f"Successfully extracted {len(parsed_data)} transactions. Choose an option below."
                                results_ready = True  # Set flag for template

                                # --- Parse dates and find range ---
                                min_date = None
                                max_date = None
                                # Added %d/%m/%y for two-digit year format
                                date_formats = [
                                    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d-%B-%Y", "%d/%m/%y"]

                                for item in parsed_json_data:
                                    date_str = item.get('date')
                                    if date_str:
                                        parsed_dt = None
                                        for fmt in date_formats:
                                            try:
                                                parsed_dt = datetime.strptime(
                                                    date_str, fmt).date()
                                                break  # Stop trying formats once one works
                                            except (ValueError, TypeError):
                                                continue  # Try next format

                                        if parsed_dt:
                                            if min_date is None or parsed_dt < min_date:
                                                min_date = parsed_dt
                                            if max_date is None or parsed_dt > max_date:
                                                max_date = parsed_dt

                                # --- Generate date range string for filename/title ---
                                date_range_string = "statement"  # Default
                                if min_date and max_date:
                                    date_range_string = f"{min_date:%Y-%m-%d}_to_{max_date:%Y-%m-%d}"
                                elif min_date:  # Only min date found
                                    date_range_string = f"from_{min_date:%Y-%m-%d}"
                                elif max_date:  # Only max date found
                                    date_range_string = f"up_to_{max_date:%Y-%m-%d}"
                                logger.debug(f"upload_pdf_view: Date range determined: {date_range_string}",
                                             extra={'request_id': request_id, 'date_range': date_range_string})

                                # Store data and date range string in session
                                logger.debug("upload_pdf_view: Storing extracted data and date range in session.", extra={
                                             'request_id': request_id})
                                # Keep date range for filenames
                                request.session['date_range_string'] = date_range_string

                                # --- Save to Database ---
                                statement_record = None
                                try:
                                    logger.info(f"upload_pdf_view: Saving extracted data to database for {pdf_file.name}.",
                                                extra={'request_id': request_id, 'pdf_filename': pdf_file.name})
                                    statement_record = StatementData.objects.create(
                                        pdf_filename=pdf_file.name if pdf_file else None,
                                        extracted_data=parsed_json_data
                                    )
                                    logger.info(f"upload_pdf_view: Data saved to database successfully. Record ID: {statement_record.id}",
                                                extra={'request_id': request_id, 'record_id': statement_record.id})
                                    # Store the ID of the record in the session
                                    request.session['statement_data_id'] = statement_record.id
                                    # Remove old full data if present
                                    request.session.pop('statement_data', None)
                                except Exception as db_error:
                                    logger.error("upload_pdf_view: Error saving data to database.",
                                                 exc_info=True, extra={'request_id': request_id, 'db_error': str(db_error)})
                                    return JsonResponse({'status': 'error', 'message': 'Failed to save statement data to database. Please try again.'}, status=500)
                                # --- End Save to Database ---
                                # --- End date parsing (moved comment for clarity) ---

                                logger.info("upload_pdf_view: AJAX request successful, returning JSON response.", extra={
                                            'request_id': request_id})
                                return JsonResponse({
                                    'status': 'success',
                                    'message': f"Successfully extracted {len(parsed_data)} transactions.",
                                    'results_ready': True
                                })
                        else:
                            logger.error(f"upload_pdf_view: Received unexpected JSON structure from Gemini API. Type: {type(parsed_data)}",
                                         extra={'request_id': request_id, 'response_type': str(type(parsed_data)), 'response_preview': cleaned_response_text[:200]})
                            return JsonResponse({'status': 'error', 'message': 'Received an unexpected data structure from the API.'}, status=500)
                    except json.JSONDecodeError:
                        logger.error("upload_pdf_view: Could not decode JSON response from Gemini API.",
                                     exc_info=True, extra={'request_id': request_id, 'raw_response': cleaned_response_text})
                        return JsonResponse({'status': 'error', 'message': 'Could not understand the response from the API (Invalid JSON).'}, status=500)

                finally:
                    if temp_file_created and file_path_for_api and os.path.exists(file_path_for_api):
                        logger.debug(f"upload_pdf_view: Removing temp file: {file_path_for_api}",
                                     extra={'request_id': request_id, 'temp_file_path': file_path_for_api})
                        os.remove(file_path_for_api)
                    # The genai.upload_file creates a File resource that might need explicit deletion
                    # depending on SDK version and how it's managed.
                    # For now, we assume the SDK handles its lifecycle or it's short-lived.
                    # If you encounter issues with too many uploaded files on the Gemini service,
                    # you might need to explicitly delete `uploaded_file_part` using `genai.delete_file(uploaded_file_part.name)`
                    # after you're done with it, but ensure it exists first.

            except Exception as e:
                logger.error("upload_pdf_view: An error occurred during PDF processing.",
                             exc_info=True, extra={'request_id': request_id, 'exception_type': type(e).__name__})
                error_message = f"An error occurred during processing: {str(e)}"
                return JsonResponse({'status': 'error', 'message': error_message}, status=500)
        else:
            # Form validation failed
            logger.warning(f"upload_pdf_view: Form validation failed. Errors: {form.errors.as_json()}",
                           extra={'request_id': request_id, 'form_errors': form.errors.as_json()})
            form_errors = form.errors.as_json()
            return JsonResponse({'status': 'error', 'message': 'Invalid form submission.', 'errors': json.loads(form_errors)}, status=400)

    # --- GET Request Handling ---
    else:
        logger.debug("upload_pdf_view: GET request received, rendering form.", extra={
                     'request_id': request_id})
        form = PDFUploadForm()
        user_friendly_message = None
        error_message = None
        results_ready = False

        # Variables to hold retrieved session values for the template
        gsheet_success_message_val = None
        gsheet_url_val = None
        gsheet_title_val = None

        # Prioritize Google Sheets specific messages
        logger.info(f"upload_pdf_view (GET): GSheet session variables ON LOAD - Message: {request.session.get('gsheet_success_message')}, URL: {request.session.get('gsheet_url')}, Title: {request.session.get('gsheet_title')}",
                    extra={'request_id': request_id,
                           'session_gsheet_success_message': request.session.get('gsheet_success_message'),
                           'session_gsheet_url': request.session.get('gsheet_url'),
                           'session_gsheet_title': request.session.get('gsheet_title')})
        _gsheet_success_message = request.session.get('gsheet_success_message')
        _upload_message = request.session.get(
            'upload_message')  # Check for general messages early

        if _gsheet_success_message:
            gsheet_success_message_val = _gsheet_success_message
            gsheet_url_val = request.session.get('gsheet_url')
            gsheet_title_val = request.session.get('gsheet_title')
            results_ready = True  # GSheet link implies results are ready for this load
            logger.debug(f"upload_pdf_view: GET with GSheet success: '{gsheet_success_message_val}', URL: {gsheet_url_val}", extra={
                         'request_id': request_id})

            # Pop GSheet specific messages
            request.session.pop('gsheet_success_message', None)
            request.session.pop('gsheet_url', None)
            request.session.pop('gsheet_title', None)

            # # Clear statement-specific data as the GSheet cycle for this PDF is complete
            # # MODIFIED: Do not clear statement_data_id and date_range_string here,
            # # so that download options remain available for the same processed statement.
            # # These are cleared when a new PDF is uploaded (see POST handling).
            # if 'statement_data_id' in request.session:
            #     logger.info(f"upload_pdf_view: (No longer clearing) statement_data_id ({request.session.get('statement_data_id')}) after GSheet success display.", extra={
            #                 'request_id': request_id})
            #     # request.session.pop('statement_data_id', None) # Keep for downloads
            # if 'date_range_string' in request.session:
            #     logger.info(f"upload_pdf_view: (No longer clearing) date_range_string ({request.session.get('date_range_string')}) after GSheet success display.", extra={
            #                 'request_id': request_id})
            #     # request.session.pop('date_range_string', None) # Keep for downloads

        elif _upload_message:  # No GSheet message, but there's a general message
            if "Error" in _upload_message:  # Simple check
                error_message = _upload_message
            else:
                user_friendly_message = _upload_message
            logger.debug(f"upload_pdf_view: GET with general message: '{_upload_message}'", extra={
                         'request_id': request_id})
            request.session.pop('upload_message', None)  # Pop after retrieving

            # If an error message is shown AND there's statement data, keep results ready
            if error_message and request.session.get('statement_data_id'):
                results_ready = True
                logger.debug(f"upload_pdf_view: General error message displayed for statement_data_id '{request.session.get('statement_data_id')}'. Setting results_ready=True.", extra={
                             'request_id': request_id})
            # If it's just a user_friendly_message (not an error) without GSheet success,
            # and statement_data_id exists, it implies a multi-step process that isn't an error.
            # Example: "PDF processed, choose download option." - results_ready should be true.
            elif user_friendly_message and request.session.get('statement_data_id'):
                results_ready = True
                logger.debug(f"upload_pdf_view: General user message displayed for statement_data_id '{request.session.get('statement_data_id')}'. Setting results_ready=True.", extra={
                             'request_id': request_id})

        # This is a "fresh" visit (no GSheet message, no general upload_message)
        else:
            logger.info("upload_pdf_view: Fresh visit (no GSheet or general messages). Clearing any old statement data.", extra={
                        'request_id': request_id})
            if 'statement_data_id' in request.session:
                logger.debug(f"upload_pdf_view: Clearing old statement_data_id: {request.session.get('statement_data_id')}", extra={
                             'request_id': request_id})
                request.session.pop('statement_data_id', None)
            if 'date_range_string' in request.session:
                logger.debug(f"upload_pdf_view: Clearing old date_range_string: {request.session.get('date_range_string')}", extra={
                             'request_id': request_id})
                request.session.pop('date_range_string', None)
            results_ready = False  # Explicitly set to false for a clean slate

        # Final check: if gsheet_success_message_val was set earlier, results_ready must be true.
        # This handles the case where it might have been turned off by the "fresh visit" logic
        # if _gsheet_success_message was true but _upload_message was also true (unlikely scenario but safe).
        if gsheet_success_message_val:
            results_ready = True

        return render(request, 'converter_app/upload_pdf.html', {
            'form': form,
            'user_message': user_friendly_message,
            'error_message': error_message,
            'results_ready': results_ready,
            'gsheet_success_message': gsheet_success_message_val,
            'gsheet_url': gsheet_url_val,
            'gsheet_title': gsheet_title_val,
        })


def download_csv_view(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.debug("Enter download_csv_view.", extra={
                 'request_id': request_id, 'path': request.path})
    statement_data_id = request.session.get('statement_data_id')
    date_range_str = request.session.get('date_range_string', 'statement')

    if not statement_data_id:
        logger.warning("download_csv_view: No statement_data_id found in session.", extra={
                       'request_id': request_id})
        # Optionally, redirect to upload page with a message
        # request.session['upload_message'] = "No data to download. Please upload a PDF first."
        # return redirect(reverse('converter_app:upload_pdf'))
        raise Http404(
            "No statement data ID found in session. Please upload a PDF first.")

    try:
        statement_record = StatementData.objects.get(id=statement_data_id)
        extracted_data = statement_record.extracted_data
        logger.info(f"download_csv_view: Retrieved statement data (ID: {statement_data_id}) for CSV generation.",
                    extra={'request_id': request_id, 'record_id': statement_data_id, 'date_range': date_range_str})
    except StatementData.DoesNotExist:
        logger.error(f"download_csv_view: StatementData with ID {statement_data_id} not found.",
                     extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404(
            "Statement data not found. It might have been cleared or an error occurred.")

    if not extracted_data:  # Should not happen if record exists and has data, but good check
        logger.warning(f"download_csv_view: StatementData record ID {statement_data_id} has no extracted_data.",
                       extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404("No extracted data available for this statement.")

    csv_data = convert_data_to_csv_string(extracted_data)

    filename = f"{date_range_str}.csv"
    logger.info(f"download_csv_view: CSV file '{filename}' prepared for download.",
                extra={'request_id': request_id, 'output_filename': filename})
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_excel_view(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.debug("Enter download_excel_view.", extra={
                 'request_id': request_id, 'path': request.path})
    statement_data_id = request.session.get('statement_data_id')
    date_range_str = request.session.get('date_range_string', 'statement')

    if not statement_data_id:
        logger.warning("download_excel_view: No statement_data_id found in session.", extra={
                       'request_id': request_id})
        raise Http404(
            "No statement data ID found in session. Please upload a PDF first.")

    try:
        statement_record = StatementData.objects.get(id=statement_data_id)
        extracted_data = statement_record.extracted_data
        logger.info(f"download_excel_view: Retrieved statement data (ID: {statement_data_id}) for Excel generation.",
                    extra={'request_id': request_id, 'record_id': statement_data_id, 'date_range': date_range_str})
    except StatementData.DoesNotExist:
        logger.error(f"download_excel_view: StatementData with ID {statement_data_id} not found.",
                     extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404(
            "Statement data not found. It might have been cleared or an error occurred.")

    if not extracted_data:
        logger.warning(f"download_excel_view: StatementData record ID {statement_data_id} has no extracted_data.",
                       extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404("No extracted data available for this statement.")

    excel_data = convert_data_to_excel_bytes(extracted_data)

    filename = f"{date_range_str}.xlsx"
    logger.info(f"download_excel_view: Excel file '{filename}' prepared for download.",
                extra={'request_id': request_id, 'output_filename': filename})
    response = HttpResponse(
        excel_data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_json_view(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.debug("Enter download_json_view.", extra={
                 'request_id': request_id, 'path': request.path})
    statement_data_id = request.session.get('statement_data_id')
    date_range_str = request.session.get('date_range_string', 'statement')

    if not statement_data_id:
        logger.warning("download_json_view: No statement_data_id found in session.", extra={
                       'request_id': request_id})
        raise Http404(
            "No statement data ID found in session. Please upload a PDF first.")

    try:
        statement_record = StatementData.objects.get(id=statement_data_id)
        extracted_data = statement_record.extracted_data
        logger.info(f"download_json_view: Retrieved statement data (ID: {statement_data_id}) for JSON generation.",
                    extra={'request_id': request_id, 'record_id': statement_data_id, 'date_range': date_range_str})
    except StatementData.DoesNotExist:
        logger.error(f"download_json_view: StatementData with ID {statement_data_id} not found.",
                     extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404(
            "Statement data not found. It might have been cleared or an error occurred.")

    if not extracted_data:
        logger.warning(f"download_json_view: StatementData record ID {statement_data_id} has no extracted_data.",
                       extra={'request_id': request_id, 'record_id': statement_data_id})
        raise Http404("No extracted data available for this statement.")

    json_string = json.dumps(extracted_data, indent=2)

    filename = f"{date_range_str}.json"
    logger.info(f"download_json_view: JSON file '{filename}' prepared for download.",
                extra={'request_id': request_id, 'output_filename': filename})
    response = HttpResponse(json_string, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# Imports for Google OAuth
# import pathlib # No longer needed for CLIENT_SECRETS_FILE

# Define the scopes required for Google Sheets access AND file creation
# Using 'drive' scope allows creating new sheets. User will need to re-authenticate.
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']
# CLIENT_SECRETS_FILE is removed as we will load from settings/environment variables.


def get_google_client_config(request):
    """
    Constructs the client_config dictionary for Google OAuth Flow
    from Django settings, which should be populated from environment variables.
    """
    redirect_uri = request.build_absolute_uri(
        reverse('converter_app:google_auth_callback'))

    # Default to standard Google URIs if not set in settings
    auth_uri = getattr(settings, 'GOOGLE_AUTH_URI',
                       "https://accounts.google.com/o/oauth2/auth")
    token_uri = getattr(settings, 'GOOGLE_TOKEN_URI',
                        "https://oauth2.googleapis.com/token")

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "redirect_uris": [redirect_uri],
            # Optional, but good practice if you have it:
            # "project_id": getattr(settings, 'GOOGLE_PROJECT_ID', None),
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
    }
    # Remove project_id if it's None to avoid issues with the library
    # if not client_config["web"]["project_id"]:
    #     del client_config["web"]["project_id"]
    return client_config


def google_auth_redirect(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.info("Enter google_auth_redirect: Initiating Google OAuth flow.",
                extra={'request_id': request_id, 'path': request.path})

    try:
        if not hasattr(settings, 'GOOGLE_CLIENT_ID') or not settings.GOOGLE_CLIENT_ID or \
           not hasattr(settings, 'GOOGLE_CLIENT_SECRET') or not settings.GOOGLE_CLIENT_SECRET:
            logger.error("google_auth_redirect: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is not configured in Django settings.",
                         extra={'request_id': request_id})
            raise ValueError(
                "Google OAuth client ID or secret is not configured on the server.")

        client_config = get_google_client_config(request)
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        # Ensure flow uses the same redirect_uri
        flow.redirect_uri = client_config['web']['redirect_uris'][0]

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        request.session['oauth_state'] = state
        logger.debug(f"google_auth_redirect: OAuth state '{state}' stored in session. Redirecting to {authorization_url}",
                     extra={'request_id': request_id, 'oauth_state': state, 'auth_url': authorization_url})
        return redirect(authorization_url)
    except ValueError as ve:  # Catch specific configuration errors
        logger.exception(f"google_auth_redirect: Configuration error for Google OAuth. Details: {str(ve)}", extra={
                         'request_id': request_id})
        request.session[
            'upload_message'] = f"Error: Google API client configuration error. {str(ve)}. Please contact support."
        return redirect(reverse('converter_app:upload_pdf'))
    except Exception as e:
        logger.exception("google_auth_redirect: Error initiating Google OAuth flow.", extra={
                         'request_id': request_id})
        request.session[
            'upload_message'] = f"Error initiating Google authentication: {str(e)}"
        return redirect(reverse('converter_app:upload_pdf'))


def google_auth_callback(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.info("Enter google_auth_callback: Handling redirect from Google.",
                extra={'request_id': request_id, 'path': request.path, 'query_params': request.GET.urlencode()})
    state = request.session.get('oauth_state')

    # Check if state matches to prevent CSRF attacks
    if not state or state != request.GET.get('state'):
        logger.warning("google_auth_callback: Invalid OAuth state parameter.",
                       extra={'request_id': request_id, 'session_state': state, 'query_state': request.GET.get('state')})
        return HttpResponse('Invalid state parameter.', status=400)

    logger.debug("google_auth_callback: OAuth state validated successfully.", extra={
                 'request_id': request_id})
    try:
        if not hasattr(settings, 'GOOGLE_CLIENT_ID') or not settings.GOOGLE_CLIENT_ID or \
           not hasattr(settings, 'GOOGLE_CLIENT_SECRET') or not settings.GOOGLE_CLIENT_SECRET:
            logger.error("google_auth_callback: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is not configured in Django settings.",
                         extra={'request_id': request_id})
            raise ValueError(
                "Google OAuth client ID or secret is not configured on the server.")

        client_config = get_google_client_config(request)
        flow = Flow.from_client_config(
            client_config, scopes=SCOPES, state=state)
        flow.redirect_uri = client_config['web']['redirect_uris'][0]

        authorization_response = request.build_absolute_uri()
        if settings.DEBUG and request.scheme == 'http':
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            logger.warning("google_auth_callback: OAUTHLIB_INSECURE_TRANSPORT enabled for local HTTP development.",
                           extra={'request_id': request_id})

        logger.debug("google_auth_callback: Fetching OAuth token.",
                     extra={'request_id': request_id})
        flow.fetch_token(authorization_response=authorization_response)
        logger.info("google_auth_callback: OAuth token fetched successfully.", extra={
                    'request_id': request_id})

        new_flow_credentials = flow.credentials
        existing_session_credentials = request.session.get(
            'google_credentials', {})
        refresh_token_to_store = new_flow_credentials.refresh_token
        if not refresh_token_to_store and existing_session_credentials:
            refresh_token_to_store = existing_session_credentials.get(
                'refresh_token')

        request.session['google_credentials'] = {
            'token': new_flow_credentials.token,
            'refresh_token': refresh_token_to_store,
            'scopes': new_flow_credentials.scopes,
            'expiry': new_flow_credentials.expiry.isoformat() if new_flow_credentials.expiry else None
            # client_id, client_secret, token_uri are not stored here as they come from settings
        }
        logger.debug("google_auth_callback: Stored relevant Google credentials (token, refresh_token, scopes, expiry) in session.",
                     extra={'request_id': request_id})
    except ValueError as ve:  # Catch specific configuration errors
        logger.exception(f"google_auth_callback: Configuration error for Google OAuth. Details: {str(ve)}", extra={
                         'request_id': request_id})
        if 'OAUTHLIB_INSECURE_TRANSPORT' in os.environ:
            del os.environ['OAUTHLIB_INSECURE_TRANSPORT']
        request.session[
            'upload_message'] = f"Error: Google API client configuration error. {str(ve)}. Please contact support."
        return redirect(reverse('converter_app:upload_pdf'))
    except Exception as e:
        logger.exception("google_auth_callback: Failed to fetch authorization token or instantiate flow.", extra={
                         'request_id': request_id})
        if 'OAUTHLIB_INSECURE_TRANSPORT' in os.environ:
            del os.environ['OAUTHLIB_INSECURE_TRANSPORT']
        # For now, just return a simple error response. Consider redirecting with a message.
        return HttpResponse(f'Failed to fetch authorization token or instantiate flow: {e}', status=400)
    # This finally block will execute regardless of whether an exception occurred in the try block or not.
    # It's a good place to clean up resources like environment variables.
    finally:
        if 'OAUTHLIB_INSECURE_TRANSPORT' in os.environ:
            logger.debug("google_auth_callback: Cleaning up OAUTHLIB_INSECURE_TRANSPORT env var.", extra={
                         'request_id': request_id})
            del os.environ['OAUTHLIB_INSECURE_TRANSPORT']
    # Removed duplicated and misplaced credential storage logic.
    # Correct logic for storing credentials in session is now within the try block above.
    next_url = request.session.pop('google_auth_next_url', None)
    redirect_target = next_url or reverse('converter_app:upload_pdf')
    
    logger.info(f"google_auth_callback: Google authentication successful. Credentials stored. Redirecting to: {redirect_target}", extra={
                'request_id': request_id, 'redirect_target': redirect_target})
    return redirect(redirect_target)

# We will add the view to actually upload to sheets next

# View to handle the actual upload to Google Sheets


def upload_to_google_sheets_view(request):
    request_id = getattr(request, 'request_id', 'N/A')
    logger.info("Enter upload_to_google_sheets_view.", extra={
                'request_id': request_id, 'path': request.path})
    credentials_dict = request.session.get('google_credentials')
    statement_data_id = request.session.get('statement_data_id')
    date_range_str = request.session.get(
        'date_range_string', 'Statement Import')

    if not statement_data_id:
        logger.warning("upload_to_google_sheets_view: No statement_data_id found in session. Redirecting to upload page.",
                       extra={'request_id': request_id})
        request.session['upload_message'] = "Error: No statement data ID found to upload. Please upload a PDF first."
        return redirect(reverse('converter_app:upload_pdf'))

    extracted_data = None
    try:
        statement_record = StatementData.objects.get(id=statement_data_id)
        extracted_data = statement_record.extracted_data
        logger.info(f"upload_to_google_sheets_view: Retrieved statement data (ID: {statement_data_id}) for Google Sheets upload.",
                    extra={'request_id': request_id, 'record_id': statement_data_id})
    except StatementData.DoesNotExist:
        logger.error(f"upload_to_google_sheets_view: StatementData with ID {statement_data_id} not found.",
                     extra={'request_id': request_id, 'record_id': statement_data_id})
        request.session['upload_message'] = "Error: Statement data not found. It might have been cleared."
        return redirect(reverse('converter_app:upload_pdf'))

    if not extracted_data:
        logger.warning(f"upload_to_google_sheets_view: StatementData record ID {statement_data_id} has no extracted_data.",
                       extra={'request_id': request_id, 'record_id': statement_data_id})
        request.session['upload_message'] = "Error: No extracted data available for this statement."
        return redirect(reverse('converter_app:upload_pdf'))

    if not credentials_dict:
        logger.info("upload_to_google_sheets_view: No Google credentials found in session. Storing current path and redirecting to auth.",
                    extra={'request_id': request_id, 'current_path': request.path})
        request.session['google_auth_next_url'] = request.path # Store current path to return after auth
        return redirect(reverse('converter_app:google_auth_redirect'))

    try:
        logger.debug("upload_to_google_sheets_view: Attempting to upload data to Google Sheets.", extra={
                     'request_id': request_id})

        # Force re-authentication if refresh_token is missing from session
        if not credentials_dict.get('refresh_token'):
            logger.warning("upload_to_google_sheets_view: Google API refresh token missing. Redirecting to auth.",
                           extra={'request_id': request_id})
            request.session['upload_message'] = "Google API refresh token is missing. Please re-authenticate."
            request.session['google_auth_next_url'] = request.path # Store current path
            return redirect(reverse('converter_app:google_auth_redirect'))

        logger.debug("upload_to_google_sheets_view: Rebuilding Google Credentials object.", extra={
                     'request_id': request_id})
        # Rebuild credentials object
        # Client configuration will be loaded from Django settings (which should load from environment variables)
        # Ensure these settings are configured in settings.py:
        # settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_TOKEN_URI

        # Check if required Google OAuth settings are available
        required_google_settings = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'GOOGLE_TOKEN_URI'
        ]
        missing_settings = [s for s in required_google_settings if not hasattr(
            settings, s) or not getattr(settings, s)]

        if missing_settings:
            logger.error(f"upload_to_google_sheets_view: Missing Google OAuth client configuration in Django settings: {', '.join(missing_settings)}",
                         extra={'request_id': request_id, 'missing_settings': missing_settings})
            request.session['upload_message'] = "Critical error: Google API client configuration is missing on the server. Please contact support."
            return redirect(reverse('converter_app:upload_pdf'))

        final_creds_args = {
            'token': credentials_dict.get('token'),
            'refresh_token': credentials_dict.get('refresh_token'),
            'scopes': credentials_dict.get('scopes'),
            'token_uri': settings.GOOGLE_TOKEN_URI,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'expiry': datetime.fromisoformat(credentials_dict['expiry']) if credentials_dict.get('expiry') else None
        }

        credentials = Credentials(**final_creds_args)

        # Check if credentials are valid (optional but good practice)
        # You might need to handle refreshing the token if it's expired
        if not credentials.valid:
            logger.info("upload_to_google_sheets_view: Google credentials are not valid. Attempting refresh.",
                        extra={'request_id': request_id, 'expired': credentials.expired, 'has_refresh_token': bool(credentials.refresh_token)})
            all_fields_present_for_refresh = all(
                [credentials.refresh_token, credentials.token_uri, credentials.client_id, credentials.client_secret])
            if credentials.expired and all_fields_present_for_refresh:
                try:
                    logger.debug("upload_to_google_sheets_view: Refreshing Google credentials.", extra={
                                 'request_id': request_id})
                    credentials.refresh(
                        google.auth.transport.requests.Request())
                    logger.info("upload_to_google_sheets_view: Google credentials refreshed successfully. Updating session.", extra={
                                'request_id': request_id})
                    request.session['google_credentials'] = {
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        # client_id, client_secret, and token_uri are static server config,
                        # no need to re-store them from the credentials object to the session.
                        # Scopes might change if incremental auth was used.
                        'scopes': credentials.scopes,
                        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
                    }
                except Exception as refresh_error:
                    logger.exception("upload_to_google_sheets_view: Failed to refresh Google credentials. Redirecting to auth.",
                                     extra={'request_id': request_id})
                    request.session['google_auth_next_url'] = request.path # Store current path
                    return redirect(reverse('converter_app:google_auth_redirect'))
            else: # This else corresponds to 'if credentials.expired and all_fields_present_for_refresh:'
                logger.warning("upload_to_google_sheets_view: Credentials not valid and cannot refresh (e.g. no refresh token). Redirecting to auth.",
                               extra={'request_id': request_id, 'expired': credentials.expired, 'has_refresh_token': bool(credentials.refresh_token)})
                request.session['google_auth_next_url'] = request.path # Store current path
                return redirect(reverse('converter_app:google_auth_redirect'))
        else:
            logger.debug("upload_to_google_sheets_view: Google credentials are valid.", extra={
                         'request_id': request_id})

        logger.debug("upload_to_google_sheets_view: Building Google Sheets API service.", extra={
                     'request_id': request_id})
        service = build('sheets', 'v4', credentials=credentials)
        sheets_api = service.spreadsheets()

        # --- Create New Spreadsheet ---
        spreadsheet_title = f"Bank Statement {date_range_str}"
        spreadsheet_body = {
            'properties': {
                'title': spreadsheet_title
            }
            # Optionally define sheet properties here if needed
        }
        try:
            logger.info(f"upload_to_google_sheets_view: Creating new Google Sheet with title '{spreadsheet_title}'.",
                        extra={'request_id': request_id, 'sheet_title': spreadsheet_title})
            spreadsheet = sheets_api.create(
                body=spreadsheet_body, fields='spreadsheetId,spreadsheetUrl').execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl')
            logger.info(f"upload_to_google_sheets_view: Google Sheet created successfully. ID: {spreadsheet_id}, URL: {spreadsheet_url}",
                        extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id, 'spreadsheet_url': spreadsheet_url})

            # --- (Optional) Rename the default 'Sheet1' ---
            logger.debug(f"upload_to_google_sheets_view: Attempting to rename default sheet to 'Transactions' for sheet ID {spreadsheet_id}.",
                         extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id})
            rename_request_body = {
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': 0,  # Default sheet usually has ID 0
                                'title': "Transactions",  # New name for the sheet
                            },
                            'fields': 'title',
                        }
                    }
                ]
            }
            try:
                sheets_api.batchUpdate(
                    spreadsheetId=spreadsheet_id, body=rename_request_body).execute()
                sheet_name_for_range = "Transactions"
                logger.info(f"upload_to_google_sheets_view: Default sheet renamed to 'Transactions' for sheet ID {spreadsheet_id}.",
                            extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id})
            except Exception as rename_error:
                logger.warning(f"upload_to_google_sheets_view: Failed to rename default sheet for sheet ID {spreadsheet_id}. Error: {rename_error}",
                               extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id, 'rename_error': str(rename_error)})
                sheet_name_for_range = "Sheet1"  # Fallback to default if rename fails

        except Exception as create_error:
            logger.exception(f"upload_to_google_sheets_view: Error creating Google Sheet.",
                             extra={'request_id': request_id, 'sheet_title': spreadsheet_title})
            request.session['upload_message'] = f"Error creating Google Sheet: {create_error}"
            return redirect(reverse('converter_app:upload_pdf'))

        logger.debug("upload_to_google_sheets_view: Preparing data for Sheets API.",
                     extra={'request_id': request_id, 'num_rows_to_write': len(extracted_data)})
        # Prepare data for Sheets API (list of lists)
        range_start = 'A1'  # Where to start writing data
        headers = ['date', 'description', 'debit', 'credit', 'balance']
        values_to_write = [headers]  # Start with header row
        for row_dict in extracted_data:  # Use extracted_data here
            # Use empty string for missing values
            row_values = [row_dict.get(header, '') for header in headers]
            values_to_write.append(row_values)

        body = {
            'values': values_to_write
        }

        # Determine the full range to write to
        # Example: If 26 data rows + 1 header row, range is A1:E27
        num_rows = len(values_to_write)
        num_cols = len(headers)
        # Convert column number to letter (e.g., 5 -> E) - simple version for few columns
        end_col_letter = chr(ord('A') + num_cols - 1) if num_cols > 0 else 'A'
        # Use the potentially renamed sheet name here
        range_name = f"'{sheet_name_for_range}'!{range_start}:{end_col_letter}{num_rows}"

        # Call the Sheets API to update values
        # valueInputOption='USER_ENTERED' tries to mimic typing data in
        logger.info(f"upload_to_google_sheets_view: Writing data to Google Sheet. ID: {spreadsheet_id}, Range: {range_name}",
                    extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id, 'range': range_name, 'num_rows': num_rows})
        result = sheets_api.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        logger.info(f"upload_to_google_sheets_view: Successfully wrote data to Google Sheet. Updated cells: {result.get('updatedCells')}",
                    extra={'request_id': request_id, 'spreadsheet_id': spreadsheet_id, 'updated_cells': result.get('updatedCells')})

        # Set session variables for the template to construct the success message safely
        request.session[
            'gsheet_success_message'] = f"Successfully uploaded {result.get('updatedCells')} cells."
        request.session['gsheet_url'] = spreadsheet_url
        request.session['gsheet_title'] = spreadsheet_title
        # Clear any generic user_message
        request.session.pop('user_message', None)
        # Clear old upload_message format
        request.session.pop('upload_message', None)
        # Explicitly mark session as modified to ensure changes save before redirect
        request.session.modified = True
    except Exception as e:
        logger.exception("upload_to_google_sheets_view: Error uploading data to Google Sheets.",
                         extra={'request_id': request_id})
        request.session['upload_message'] = f"Error uploading to Google Sheets: {e}"

    logger.info(f"upload_to_google_sheets_view: GSheet success session PRE-REDIRECT - Message: {request.session.get('gsheet_success_message')}, URL: {request.session.get('gsheet_url')}, Title: {request.session.get('gsheet_title')}",
                extra={'request_id': request_id,
                       'session_gsheet_success_message': request.session.get('gsheet_success_message'),
                       'session_gsheet_url': request.session.get('gsheet_url'),
                       'session_gsheet_title': request.session.get('gsheet_title')})
    logger.debug("upload_to_google_sheets_view: Upload process finished, redirecting to upload_pdf.", extra={
                 'request_id': request_id})
    # Clear session data after attempting upload? Optional.
    # if 'statement_data' in request.session:
    #     del request.session['statement_data']
    # if 'google_credentials' in request.session: # Keep credentials for future uploads?
    #     pass

    return redirect(reverse('converter_app:upload_pdf'))  # Redirect back
