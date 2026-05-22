from __future__ import annotations

from extractor.constants import MAX_DOCX_UNCOMPRESSED_SIZE, MAX_FILE_SIZE

EMPTY_FILE_MESSAGE = "Empty file"
EXTRACTION_FAILED_MESSAGE = "Extraction failed"
INVALID_BASE64_BODY_MESSAGE = "Invalid base64-encoded request body"
INVALID_FORM_BODY_MESSAGE = "Invalid form request body"
INVALID_JSON_BODY_MESSAGE = "Invalid JSON request body"
INVALID_REQUEST_BODY_MESSAGE = "Invalid request body"
INVALID_REQUEST_EVENT_MESSAGE = "Invalid request event"
INVALID_DOCX_ARCHIVE_MESSAGE = (
    "Unsupported file: expected PDF or DOCX (invalid DOCX archive)"
)
MISSING_FILE_MESSAGE = (
    "No file provided. Send a PDF or DOCX as multipart form field 'file' "
    "or provide 'file_url'"
)
POST_INSTRUCTIONS = (
    "Use POST to upload a PDF or DOCX as multipart form field 'file' "
    "or provide 'file_url'"
)
UNSUPPORTED_DOCUMENT_FORMAT_MESSAGE = "Unsupported document format"


def file_too_large_message() -> str:
    return f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB"


def docx_archive_too_large_message() -> str:
    return (
        "DOCX archive expands beyond the maximum supported size "
        f"of {MAX_DOCX_UNCOMPRESSED_SIZE // (1024 * 1024)} MB"
    )


def unsupported_file_message(content_type: str | None) -> str:
    return f"Unsupported file: expected PDF or DOCX (content-type {content_type!r})"


def extraction_format_failed_message(format_label: str) -> str:
    return (
        "Failed to extract "
        f"{format_label} content from a valid-looking {format_label} file"
    )


def downloaded_file_too_large_message(max_file_size: int) -> str:
    return (
        "Downloaded file exceeds maximum size of "
        f"{max_file_size // (1024 * 1024)} MB"
    )
