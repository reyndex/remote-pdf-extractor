from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from core import MAX_FILE_SIZE, error_payload, normalize_content_type, process_upload
from remote_file import RemoteFileError, download_file_url
from request_payload import (
    MISSING_FILE_MESSAGE,
    POST_INSTRUCTIONS,
    file_url_from_json_body,
    file_url_from_urlencoded_body,
    parse_multipart_upload,
)


def _lambda_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {
            "content-type": "application/json",
        },
        "body": json.dumps(payload),
    }


def _request_method(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext", {})
    if isinstance(request_context, dict):
        http_context = request_context.get("http", {})
        if isinstance(http_context, dict):
            method = http_context.get("method")
            if isinstance(method, str):
                return method

    method = event.get("httpMethod")
    return method if isinstance(method, str) else ""


def _header_value(headers: object, name: str) -> str:
    if not isinstance(headers, dict):
        return ""
    name_lower = name.lower()
    for key, value in headers.items():
        if (
            isinstance(key, str)
            and key.lower() == name_lower
            and isinstance(value, str)
        ):
            return value
    return ""


def _decode_body(event: dict[str, Any]) -> bytes:
    body = event.get("body", "")
    if not isinstance(body, str):
        raise ValueError("Invalid request body")
    if event.get("isBase64Encoded"):
        try:
            return base64.b64decode(body, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Invalid base64-encoded request body") from exc
    return body.encode("utf-8")


def _process_file_url(file_url: str) -> dict[str, Any]:
    try:
        file_bytes, content_type = download_file_url(
            file_url, max_file_size=MAX_FILE_SIZE
        )
    except RemoteFileError as exc:
        return error_payload(str(exc))
    return process_upload(file_bytes, content_type)


def handler(event, _context):
    if not isinstance(event, dict):
        return _lambda_response(error_payload("Invalid request event"))

    if _request_method(event) != "POST":
        return _lambda_response(error_payload(POST_INSTRUCTIONS))

    content_type = _header_value(event.get("headers"), "content-type")
    normalized_content_type = normalize_content_type(content_type)
    try:
        body = _decode_body(event)
    except ValueError as exc:
        return _lambda_response(error_payload(str(exc)))

    if normalized_content_type == "multipart/form-data":
        upload = parse_multipart_upload(body, content_type)
        if upload.file_bytes is not None:
            file_bytes = upload.file_bytes
            file_content_type = upload.file_content_type
        elif upload.file_url is not None:
            return _lambda_response(_process_file_url(upload.file_url))
        else:
            return _lambda_response(error_payload(MISSING_FILE_MESSAGE))
    elif normalized_content_type == "application/json":
        try:
            file_url = file_url_from_json_body(body)
        except ValueError as exc:
            return _lambda_response(error_payload(str(exc)))
        if file_url is None:
            return _lambda_response(error_payload(MISSING_FILE_MESSAGE))
        return _lambda_response(_process_file_url(file_url))
    elif normalized_content_type == "application/x-www-form-urlencoded":
        try:
            file_url = file_url_from_urlencoded_body(body)
        except ValueError as exc:
            return _lambda_response(error_payload(str(exc)))
        if file_url is None:
            return _lambda_response(error_payload(MISSING_FILE_MESSAGE))
        return _lambda_response(_process_file_url(file_url))
    else:
        file_bytes = body
        file_content_type = content_type

    return _lambda_response(process_upload(file_bytes, file_content_type))
