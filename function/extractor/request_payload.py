from __future__ import annotations

import json
from dataclasses import dataclass
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from typing import Any
from urllib.parse import parse_qs

from extractor.enums import UploadRequestField
from extractor.errors import INVALID_FORM_BODY_MESSAGE, INVALID_JSON_BODY_MESSAGE


@dataclass(frozen=True)
class MultipartUpload:
    file_bytes: bytes | None = None
    file_content_type: str | None = None
    file_url: str | None = None


def _text_field_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def file_url_from_mapping(mapping: Any) -> str | None:
    if not hasattr(mapping, "get"):
        return None
    return _text_field_value(mapping.get(UploadRequestField.FILE_URL.value))


def file_url_from_json_body(body: bytes) -> str | None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(INVALID_JSON_BODY_MESSAGE) from exc

    if not isinstance(payload, dict):
        return None
    return file_url_from_mapping(payload)


def file_url_from_urlencoded_body(body: bytes) -> str | None:
    try:
        decoded_body = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(INVALID_FORM_BODY_MESSAGE) from exc

    values = parse_qs(decoded_body, keep_blank_values=True).get(
        UploadRequestField.FILE_URL.value
    )
    if not values:
        return None
    return _text_field_value(values[0])


def _multipart_text_value(part: Message) -> str | None:
    payload = part.get_payload(decode=True)
    if payload is None:
        return _text_field_value(part.get_content())

    charset = part.get_content_charset() or "utf-8"
    try:
        decoded = payload.decode(charset)
    except (LookupError, UnicodeDecodeError):
        decoded = payload.decode("utf-8", errors="replace")
    return _text_field_value(decoded)


def parse_multipart_upload(body: bytes, content_type: str) -> MultipartUpload:
    # Strip CRLF from the caller-supplied header value before splicing it into
    # a synthetic MIME envelope; prevents header injection via Content-Type.
    safe_content_type = content_type.replace("\r", "").replace("\n", "")
    message = BytesParser(policy=default).parsebytes(
        (
            f"Content-Type: {safe_content_type}\r\n"
            "MIME-Version: 1.0\r\n\r\n"
        ).encode("utf-8")
        + body
    )

    if not message.is_multipart():
        return MultipartUpload()

    file_url: str | None = None
    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue

        field_name = part.get_param("name", header="content-disposition")
        if field_name == UploadRequestField.FILE.value:
            return MultipartUpload(
                file_bytes=part.get_payload(decode=True) or b"",
                file_content_type=part.get_content_type(),
            )
        if field_name == UploadRequestField.FILE_URL.value and file_url is None:
            file_url = _multipart_text_value(part)

    return MultipartUpload(file_url=file_url)
