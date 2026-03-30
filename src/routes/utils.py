"""Shared utility helpers for route handlers."""

import base64

from flask import jsonify


def pdf_success_response(report_path, message='Report generated successfully'):
    """Read a PDF file and return a JSON response with base64-encoded content."""
    with open(report_path, 'rb') as pdf_file:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
    return jsonify({
        'status': 'success',
        'message': message,
        'file_path': str(report_path),
        'pdf_base64': pdf_base64,
    })
