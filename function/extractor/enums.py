from __future__ import annotations

from enum import StrEnum


class ExtractionResultStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class DocumentFormat(StrEnum):
    PDF = "PDF"
    DOCX = "DOCX"


class UploadRequestField(StrEnum):
    FILE = "file"
    FILE_URL = "file_url"
