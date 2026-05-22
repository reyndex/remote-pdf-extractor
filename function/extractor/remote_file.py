from __future__ import annotations

from http.client import InvalidURL
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from extractor.errors import downloaded_file_too_large_message

DOWNLOAD_CHUNK_SIZE = 64 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30
USER_AGENT = "remote-pdf-extractor/1.0"
ALLOWED_DOWNLOAD_SCHEMES = ("http", "https")


class RemoteFileError(ValueError):
    pass


def _validated_http_url(file_url: str, *, redirect: bool = False) -> str:
    trimmed_url = file_url.strip()
    try:
        parsed = urlparse(trimmed_url)
    except ValueError as exc:
        raise RemoteFileError("file_url must be a valid URL") from exc
    if parsed.scheme.lower() not in ALLOWED_DOWNLOAD_SCHEMES or not parsed.netloc:
        if redirect:
            raise RemoteFileError("file_url redirected to a non-http URL")
        raise RemoteFileError("file_url must be an http or https URL")
    return trimmed_url


def _content_length(headers: object) -> int | None:
    if not hasattr(headers, "get"):
        return None
    raw_value = headers.get("content-length")
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _content_type(headers: object) -> str | None:
    if not hasattr(headers, "get"):
        return None
    raw_value = headers.get("content-type")
    return raw_value if isinstance(raw_value, str) else None


def download_file_url(
    file_url: str,
    *,
    max_file_size: int,
    timeout_seconds: int = DOWNLOAD_TIMEOUT_SECONDS,
) -> tuple[bytes, str | None]:
    try:
        url = _validated_http_url(file_url)
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=timeout_seconds) as response:
            _validated_http_url(response.geturl(), redirect=True)
            declared_size = _content_length(response.headers)
            if declared_size is not None and declared_size > max_file_size:
                raise RemoteFileError(downloaded_file_too_large_message(max_file_size))

            chunks: list[bytes] = []
            total_size = 0
            while chunk := response.read(DOWNLOAD_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > max_file_size:
                    raise RemoteFileError(
                        downloaded_file_too_large_message(max_file_size)
                    )
                chunks.append(chunk)

            return b"".join(chunks), _content_type(response.headers)
    except RemoteFileError:
        raise
    except HTTPError as exc:
        raise RemoteFileError(f"Unable to download file_url: HTTP {exc.code}") from exc
    except TimeoutError as exc:
        raise RemoteFileError("Unable to download file_url: request timed out") from exc
    except (InvalidURL, ValueError) as exc:
        raise RemoteFileError("file_url must be a valid URL") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RemoteFileError(f"Unable to download file_url: {reason}") from exc
    except OSError as exc:
        raise RemoteFileError(f"Unable to download file_url: {exc}") from exc
