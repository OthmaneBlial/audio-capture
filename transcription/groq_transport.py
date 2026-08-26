"""Small stdlib HTTP transport for Groq's OpenAI-compatible audio endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from typing import Any, Optional


class GroqTransportError(RuntimeError):
    """HTTP boundary error with no response body or credential material."""


class GroqHTTPTransport:
    BASE_URL = "https://api.groq.com/openai/v1/audio"

    def __init__(
        self,
        *,
        api_key: str,
        timeout: float = 25.0,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._opener = opener

    def transcribe(
        self,
        wav_data: bytes,
        *,
        model: str,
        language: Optional[str],
        translate: bool,
    ) -> str:
        endpoint = "translations" if translate else "transcriptions"
        fields = {"model": model, "response_format": "json"}
        if language and not translate:
            fields["language"] = language
        body, content_type = self._multipart(fields, wav_data)
        request = urllib.request.Request(
            f"{self.BASE_URL}/{endpoint}",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
                "Content-Type": content_type,
                "User-Agent": "voice-transcriber/1",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            status_code = error.code
            # Python 3.9's HTTPError.close() assumes a response file exists;
            # test doubles and some failed connection paths legitimately have
            # no body handle. Never read a provider error body, and close the
            # handle only when one was supplied.
            if error.fp is not None:
                error.close()
            raise GroqTransportError(f"Groq returned HTTP {status_code}.") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise GroqTransportError("Could not reach Groq before the request timeout.") from error
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GroqTransportError("Groq returned an unreadable response.") from error
        text = decoded.get("text") if isinstance(decoded, dict) else None
        if not isinstance(text, str):
            raise GroqTransportError("Groq returned a response without transcript text.")
        return text

    @staticmethod
    def _multipart(fields: dict[str, str], wav_data: bytes) -> tuple[bytes, str]:
        boundary = f"voice-transcriber-{uuid.uuid4().hex}"
        boundary_bytes = boundary.encode("ascii")
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend(
                [
                    b"--" + boundary_bytes + b"\r\n",
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
                    value.encode("utf-8"),
                    b"\r\n",
                ]
            )
        chunks.extend(
            [
                b"--" + boundary_bytes + b"\r\n",
                b'Content-Disposition: form-data; name="file"; filename="speech.wav"\r\n',
                b"Content-Type: audio/wav\r\n\r\n",
                wav_data,
                b"\r\n--" + boundary_bytes + b"--\r\n",
            ]
        )
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
