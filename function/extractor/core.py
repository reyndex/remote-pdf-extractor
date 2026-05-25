from __future__ import annotations

import io
import logging
import os
import re
import tempfile
import zipfile
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree as ET

import mammoth
import markdownify
import phonenumbers
import pymupdf
import pymupdf4llm
import urlextract
from bs4 import BeautifulSoup

from extractor.constants import (
    MAX_DOCX_UNCOMPRESSED_SIZE,
    MAX_FILE_SIZE,
    ZIP_READ_CHUNK_SIZE,
)
from extractor.enums import DocumentFormat, ExtractionErrorCode
from extractor.errors import (
    EMPTY_FILE_MESSAGE,
    EXTRACTION_FAILED_MESSAGE,
    INVALID_DOCX_ARCHIVE_MESSAGE,
    UNSUPPORTED_DOCUMENT_FORMAT_MESSAGE,
    docx_archive_too_large_message,
    extraction_format_failed_message,
    file_too_large_message,
    unsupported_file_message,
)
from extractor.response_schema import (
    ExtractionData,
    ExtractionResponse,
)

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
DOCX_CONTENT_MEMBER = "word/document.xml"

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)\+?(?:\(\d+\)|\d)[\d().\-\s]{5,}\d(?!\w)")
HOSTNAME_WITH_TLD_RE = re.compile(r"^(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}$")

URL_SCHEME_PREFIXES = ("https://", "http://")
_URL_CACHE_DIR = os.path.join(tempfile.gettempdir(), "urlextract")
os.makedirs(_URL_CACHE_DIR, exist_ok=True)
URL_EXTRACTOR = urlextract.URLExtract(cache_dir=_URL_CACHE_DIR)

MARKDOWNIFY_OPTIONS = {
    "heading_style": "ATX",
    "bullets": "-",
    "strip": ["script", "style"],
    "escape_asterisks": False,
    "escape_underscores": False,
    "escape_misc": False,
    "strong_em_symbol": "*",
    "code_language": "",
}

HYPERLINK_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)
EXTERNAL_URL_PREFIXES = ("http://", "https://", "mailto:", "tel:")
logger = logging.getLogger(__name__)


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def error_payload(
    message: str,
    *,
    code: ExtractionErrorCode = ExtractionErrorCode.INVALID_REQUEST,
) -> ExtractionResponse:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": {},
        },
    }


def success_payload(data: ExtractionData) -> ExtractionResponse:
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def detect_format(file_bytes: bytes) -> DocumentFormat | None:
    if file_bytes.startswith(PDF_MAGIC):
        return DocumentFormat.PDF
    if file_bytes.startswith(ZIP_MAGIC) and _is_docx_zip(file_bytes):
        return DocumentFormat.DOCX
    return None


def _is_docx_zip(file_bytes: bytes) -> bool:
    # ZIP magic is shared by every OOXML, ODF, and plain zip. Confirm the
    # archive is a Word document by checking for its primary content part.
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            return DOCX_CONTENT_MEMBER in z.namelist()
    except zipfile.BadZipFile:
        return False


def process_upload(file_bytes: bytes, content_type: str | None) -> ExtractionResponse:
    if len(file_bytes) == 0:
        return error_payload(
            EMPTY_FILE_MESSAGE,
            code=ExtractionErrorCode.EMPTY_FILE,
        )
    if len(file_bytes) > MAX_FILE_SIZE:
        return error_payload(
            file_too_large_message(),
            code=ExtractionErrorCode.FILE_TOO_LARGE,
        )
    document_format = detect_format(file_bytes)
    if document_format is None:
        return error_payload(
            unsupported_file_message(content_type),
            code=ExtractionErrorCode.UNSUPPORTED_DOCUMENT_FORMAT,
        )
    try:
        return success_payload(_extract_document(file_bytes, document_format))
    except ValueError as exc:
        message = str(exc)
        if message == docx_archive_too_large_message():
            code = ExtractionErrorCode.FILE_TOO_LARGE
        elif message in {
            INVALID_DOCX_ARCHIVE_MESSAGE,
            extraction_format_failed_message(DocumentFormat.PDF.value),
            extraction_format_failed_message(DocumentFormat.DOCX.value),
        }:
            code = ExtractionErrorCode.MALFORMED_FILE
        else:
            code = ExtractionErrorCode.EXTRACTION_FAILED
        return error_payload(message, code=code)
    except Exception:
        logger.exception(EXTRACTION_FAILED_MESSAGE)
        return error_payload(
            EXTRACTION_FAILED_MESSAGE,
            code=ExtractionErrorCode.EXTRACTION_FAILED,
        )


def _unique_preserving_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _extract_emails(text: str) -> list[str]:
    return _unique_preserving_order(EMAIL_RE.findall(text))


def _normalize_phone(raw_phone: str) -> str:
    digits = re.sub(r"\D", "", raw_phone)
    if raw_phone.lstrip().startswith("+"):
        return f"+{digits}"
    return digits


def _is_local_phone_candidate(raw_phone: str) -> bool:
    digit_groups = re.findall(r"\d+", raw_phone)
    digit_count = sum(len(group) for group in digit_groups)
    if digit_count > 15:
        return False

    # No default region guessing. Keep local-format numbers only when they look
    # meaningfully phone-like instead of short numeric fragments such as years.
    return digit_count >= 9 or (digit_count >= 8 and len(digit_groups) >= 4)


def _overlaps_any(span: tuple[int, int], other_spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(
        start < other_end and other_start < end
        for other_start, other_end in other_spans
    )


def _extract_phones(text: str) -> list[str]:
    phone_numbers: list[str] = []
    matched_spans: list[tuple[int, int]] = []

    for match in phonenumbers.PhoneNumberMatcher(text, None):
        phone_numbers.append(
            phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.E164
            )
        )
        matched_spans.append((match.start, match.end))

    for match in PHONE_CANDIDATE_RE.finditer(text):
        raw_phone = match.group(0)
        if raw_phone.lstrip().startswith("+"):
            continue
        if _overlaps_any((match.start(), match.end()), matched_spans):
            continue
        if not _is_local_phone_candidate(raw_phone):
            continue
        phone_numbers.append(_normalize_phone(raw_phone))

    return _unique_preserving_order(phone_numbers)


def _is_real_url(url: str) -> bool:
    # Accept http-like URLs only. Rejects non-http schemes (tel:, mailto:,
    # javascript:, ftp:, ...) and tech acronyms like ASP.NET / Node.js that
    # urlextract picks up via TLD match.
    lower = url.lower()
    if lower.startswith(URL_SCHEME_PREFIXES):
        return True
    if lower.startswith("www."):
        return True
    head, sep, _ = url.partition("/")
    return bool(sep) and ":" not in head and bool(HOSTNAME_WITH_TLD_RE.fullmatch(head))


def _extract_text_urls(text: str) -> list[str]:
    return URL_EXTRACTOR.find_urls(text, only_unique=True)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return urlunparse(
        parsed._replace(scheme="https", query="", path=parsed.path.rstrip("/"))
    )


def _combine_link_urls(
    annotation_link_urls: list[str], text_urls: list[str]
) -> list[str]:
    seen: set[str] = set()
    combined_link_urls: list[str] = []
    for url in [*annotation_link_urls, *text_urls]:
        if not _is_real_url(url):
            continue
        normalized = _normalize_url(url)
        if normalized in seen:
            continue
        seen.add(normalized)
        combined_link_urls.append(normalized)
    return combined_link_urls


def _extract_pdf_annotation_link_urls(doc: pymupdf.Document) -> list[str]:
    link_urls: list[str] = []
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if uri:
                link_urls.append(uri)
    return _unique_preserving_order(link_urls)


def _collect_docx_hyperlink_urls(archive: zipfile.ZipFile) -> list[str]:
    link_urls: list[str] = []
    for name in archive.namelist():
        if not name.endswith(".rels"):
            continue
        try:
            root = ET.fromstring(archive.read(name))
        except ET.ParseError:
            continue
        for rel in root:
            if rel.attrib.get("Type") != HYPERLINK_REL_TYPE:
                continue
            target = rel.attrib.get("Target", "")
            if target.startswith(EXTERNAL_URL_PREFIXES):
                link_urls.append(target)
    return _unique_preserving_order(link_urls)


def _check_docx_archive_size(archive: zipfile.ZipFile) -> None:
    total_uncompressed_size = 0
    try:
        for info in archive.infolist():
            if info.is_dir():
                continue
            with archive.open(info) as member:
                while chunk := member.read(ZIP_READ_CHUNK_SIZE):
                    total_uncompressed_size += len(chunk)
                    if total_uncompressed_size > MAX_DOCX_UNCOMPRESSED_SIZE:
                        raise ValueError(docx_archive_too_large_message())
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise ValueError(INVALID_DOCX_ARCHIVE_MESSAGE) from exc


def _flatten_layout_tables(html_str: str) -> str:
    # Word resumes commonly use tables as a layout grid. Pipe-table markdown
    # from those is unreadable, so drop the table and render each non-empty
    # cell as a standalone block.
    soup = BeautifulSoup(html_str, "html.parser")
    for table in soup.find_all("table"):
        container = soup.new_tag("div")
        for cell in table.find_all(["td", "th"]):
            if not cell.get_text(strip=True):
                continue
            block = soup.new_tag("div")
            for child in list(cell.contents):
                block.append(child.extract())
            container.append(block)
        table.replace_with(container)
    return str(soup)


def _extract_pdf(file_bytes: bytes) -> tuple[str, list[str]]:
    with pymupdf.open(
        stream=file_bytes, filetype=DocumentFormat.PDF.value.lower()
    ) as doc:
        markdown = pymupdf4llm.to_markdown(doc, show_progress=False)
        return markdown, _extract_pdf_annotation_link_urls(doc)


def _extract_docx(file_bytes: bytes) -> tuple[str, list[str]]:
    # Open the archive once for both the zip-bomb safety check and hyperlink
    # harvesting; mammoth opens its own handle for decoding.
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        _check_docx_archive_size(archive)
        link_urls = _collect_docx_hyperlink_urls(archive)
    result = mammoth.convert_to_html(io.BytesIO(file_bytes))
    html_flat = _flatten_layout_tables(result.value)
    markdown = markdownify.markdownify(html_flat, **MARKDOWNIFY_OPTIONS)
    return markdown, link_urls


_FORMAT_EXTRACTORS = {
    DocumentFormat.PDF: _extract_pdf,
    DocumentFormat.DOCX: _extract_docx,
}


def _extract_for_format(
    file_bytes: bytes, document_format: DocumentFormat
) -> tuple[str, list[str]]:
    extractor = _FORMAT_EXTRACTORS.get(document_format)
    if extractor is None:
        raise ValueError(UNSUPPORTED_DOCUMENT_FORMAT_MESSAGE)
    format_label = document_format.value
    try:
        return extractor(file_bytes)
    except ValueError:
        raise
    except Exception:
        logger.exception("%s extraction failed", format_label)
        raise ValueError(extraction_format_failed_message(format_label)) from None


def _extract_document(
    file_bytes: bytes, document_format: DocumentFormat
) -> ExtractionData:
    markdown, annotation_link_urls = _extract_for_format(file_bytes, document_format)

    haystack = "\n".join([markdown, *annotation_link_urls])
    return {
        "markdown": markdown,
        "email_addresses": _extract_emails(haystack),
        "link_urls": _combine_link_urls(
            annotation_link_urls, _extract_text_urls(markdown)
        ),
        "phone_numbers": _extract_phones(haystack),
    }
