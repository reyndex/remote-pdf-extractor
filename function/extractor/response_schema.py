from __future__ import annotations

from typing import Literal, TypedDict

from extractor.enums import ExtractionErrorCode

SUCCESS_STATUS_CODE = 200
BAD_REQUEST_STATUS_CODE = 400
INTERNAL_ERROR_STATUS_CODE = 500


class ExtractionData(TypedDict):
    markdown: str
    email_addresses: list[str]
    link_urls: list[str]
    phone_numbers: list[str]


class ApiError(TypedDict):
    code: ExtractionErrorCode
    message: str
    details: dict[str, object]


class ExtractionSuccessResponse(TypedDict):
    ok: Literal[True]
    data: ExtractionData
    error: None


class ExtractionErrorResponse(TypedDict):
    ok: Literal[False]
    data: None
    error: ApiError


ExtractionResponse = ExtractionSuccessResponse | ExtractionErrorResponse


def http_status_code_for_response(payload: ExtractionResponse) -> int:
    if payload["ok"]:
        return SUCCESS_STATUS_CODE
    if payload["error"]["code"] == ExtractionErrorCode.EXTRACTION_FAILED:
        return INTERNAL_ERROR_STATUS_CODE
    return BAD_REQUEST_STATUS_CODE
