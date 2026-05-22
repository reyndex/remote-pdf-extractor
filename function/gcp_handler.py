from __future__ import annotations

import functions_framework
from extractor.constants import MAX_FILE_SIZE
from extractor.core import error_payload, normalize_content_type, process_upload
from extractor.enums import UploadRequestField
from extractor.errors import MISSING_FILE_MESSAGE, POST_INSTRUCTIONS
from extractor.remote_file import RemoteFileError, download_file_url
from extractor.request_payload import (
    file_url_from_json_body,
    file_url_from_mapping,
)
from flask import jsonify


def _file_url_from_request(request, normalized_content_type: str) -> str | None:
    file_url = file_url_from_mapping(request.form)
    if file_url is not None:
        return file_url

    if normalized_content_type != "application/json":
        return None

    return file_url_from_json_body(request.get_data())


def _process_file_url(file_url: str):
    try:
        file_bytes, content_type = download_file_url(
            file_url, max_file_size=MAX_FILE_SIZE
        )
    except RemoteFileError as exc:
        return error_payload(str(exc))
    return process_upload(file_bytes, content_type)


@functions_framework.http
def extract_document(request):
    if request.method != "POST":
        return jsonify(error_payload(POST_INSTRUCTIONS))

    normalized_content_type = normalize_content_type(request.content_type)
    if normalized_content_type == "multipart/form-data":
        uploaded_file = request.files.get(UploadRequestField.FILE.value)
        if uploaded_file is not None:
            return jsonify(
                process_upload(uploaded_file.read(), uploaded_file.content_type)
            )

    try:
        file_url = _file_url_from_request(request, normalized_content_type)
    except ValueError as exc:
        return jsonify(error_payload(str(exc)))

    if file_url is None:
        return jsonify(error_payload(MISSING_FILE_MESSAGE))

    return jsonify(_process_file_url(file_url))
