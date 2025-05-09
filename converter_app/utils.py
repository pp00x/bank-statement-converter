import csv
import io
import openpyxl  # We'll install this next


def sanitize_for_formula_injection(value):
    """Prepends a single quote to string values that start with formula-like characters."""
    if value and isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def convert_data_to_csv_string(data_list):
    """
    Converts a list of dictionaries (transactions) to a CSV formatted string.
    """
    if not data_list:
        return ""
    output = io.StringIO()
    fieldnames = ['date', 'description', 'debit', 'credit', 'balance']

    processed_data_list = []
    for row_data in data_list:
        # Sanitize each value in the row
        processed_row = {key: sanitize_for_formula_injection(
            row_data.get(key)) for key in fieldnames}
        processed_data_list.append(processed_row)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(processed_data_list)
    return output.getvalue()


def convert_data_to_excel_bytes(data_list):
    """
    Converts a list of dictionaries (transactions) to Excel (XLSX) format as bytes.
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    headers = ['date', 'description', 'debit', 'credit', 'balance']
    sheet.append(headers)  # Always append headers

    if data_list:  # Only append data rows if data_list is not empty
        for row_dict in data_list:
            # Ensure all keys are present, defaulting to None if missing from a specific dict
            # Sanitize each value before appending
            row_values = [sanitize_for_formula_injection(
                row_dict.get(header)) for header in headers]
            sheet.append(row_values)

    excel_bytes = io.BytesIO()
    workbook.save(excel_bytes)
    excel_bytes.seek(0)
    return excel_bytes.getvalue()
