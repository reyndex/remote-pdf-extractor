from __future__ import annotations

from typing import TypedDict

from extractor.enums import ExtractionResultStatus


class ExtractionData(TypedDict):
    markdown: str
    email_addresses: list[str]
    link_urls: list[str]
    phone_numbers: list[str]


class ExtractionResponse(TypedDict):
    status: ExtractionResultStatus
    data: ExtractionData | str
