from __future__ import annotations

from enum import StrEnum


class ExtractionErrorCode(StrEnum):
    EMPTY_FILE = "empty_file"
    EXTRACTION_FAILED = "extraction_failed"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_REQUEST = "invalid_request"
    MALFORMED_FILE = "malformed_file"
    MISSING_FILE = "missing_file"
    REMOTE_FILE_DOWNLOAD_FAILED = "remote_file_download_failed"
    UNSUPPORTED_DOCUMENT_FORMAT = "unsupported_document_format"


class DocumentFormat(StrEnum):
    PDF = "PDF"
    DOCX = "DOCX"


class UploadRequestField(StrEnum):
    FILE = "file"
    FILE_URL = "file_url"
