from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from .errors import (
    InvalidURLError,
    UnsupportedSourceError,
)


class URLNormalizer:
    """
    Strict YouTube URL normalization.

    Supported:

    https://www.youtube.com/watch?v=VIDEO_ID
    https://youtu.be/VIDEO_ID
    https://www.youtube.com/shorts/VIDEO_ID
    https://www.youtube.com/embed/VIDEO_ID
    https://www.youtube.com/live/VIDEO_ID
    """

    ALLOWED_HOSTNAMES = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    }

    VIDEO_ID_RE = re.compile(
        r"^[A-Za-z0-9_-]{11}$"
    )

    @classmethod
    def validate_and_normalize(
        cls,
        url: str,
    ) -> dict[str, str]:

        if not isinstance(url, str):
            raise InvalidURLError(
                "URL must be a string."
            )

        url = url.strip()

        if not url:
            raise InvalidURLError(
                "URL cannot be empty."
            )

        parsed = urlparse(url)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise InvalidURLError(
                "URL must use HTTP or HTTPS."
            )

        hostname = (
            parsed.hostname or ""
        ).lower().rstrip(".")

        if hostname not in cls.ALLOWED_HOSTNAMES:
            raise UnsupportedSourceError(
                f"Unsupported hostname: {hostname}"
            )

        video_id = cls.extract_video_id(
            parsed,
            hostname,
        )

        if not cls.VIDEO_ID_RE.fullmatch(
            video_id
        ):
            raise InvalidURLError(
                "Invalid YouTube video ID."
            )

        return {
            "source": "youtube",
            "video_id": video_id,
        }

    @classmethod
    def extract_video_id(
        cls,
        parsed,
        hostname: str,
    ) -> str:

        path = parsed.path or ""

        # youtu.be/VIDEO_ID
        if hostname == "youtu.be":

            parts = [
                part
                for part in path.split("/")
                if part
            ]

            if len(parts) != 1:
                raise InvalidURLError(
                    "Invalid youtu.be URL."
                )

            return parts[0]

        query = parse_qs(
            parsed.query,
            keep_blank_values=True,
        )

        # youtube.com/watch?v=VIDEO_ID
        if path == "/watch":

            values = query.get("v", [])

            if (
                len(values) != 1
                or not values[0]
            ):
                raise InvalidURLError(
                    "Watch URL must contain exactly one video ID."
                )

            return values[0]

        # /shorts/VIDEO_ID
        # /embed/VIDEO_ID
        # /live/VIDEO_ID
        for prefix in (
            "/shorts/",
            "/embed/",
            "/live/",
        ):

            if path.startswith(prefix):

                remaining = path[
                    len(prefix):
                ]

                parts = [
                    part
                    for part in remaining.split("/")
                    if part
                ]

                if len(parts) != 1:
                    raise InvalidURLError(
                        "Invalid YouTube video path."
                    )

                return parts[0]

        raise InvalidURLError(
            "Unsupported YouTube URL format."
        )
