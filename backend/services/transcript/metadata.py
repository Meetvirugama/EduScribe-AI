from __future__ import annotations

import asyncio
import os
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .errors import (
    MetadataAcquisitionError,
)


class MetadataAcquisition:

    DEFAULT_PLAYER_CLIENTS = (
        "web",
    )

    @classmethod
    async def fetch_metadata(
        cls,
        url: str,
        *,
        player_clients: tuple[str, ...] | None = None,
        cookie_file: str | None = None,
        max_duration_seconds: int | None = None,
    ) -> dict[str, Any]:

        options = cls._build_options(
            player_clients=player_clients,
            cookie_file=cookie_file,
        )

        def _fetch():

            try:

                with YoutubeDL(
                    options
                ) as ydl:

                    info = ydl.extract_info(
                        url,
                        download=False,
                    )

                    if not info:

                        raise MetadataAcquisitionError(
                            "VIDEO_NOT_FOUND",
                            "No metadata returned.",
                            False,
                        )

                    duration = info.get(
                        "duration"
                    )

                    if duration is not None:

                        try:
                            duration = float(
                                duration
                            )

                        except (
                            TypeError,
                            ValueError,
                        ):

                            duration = None

                    if (
                        max_duration_seconds
                        is not None
                        and duration is not None
                        and duration
                        > max_duration_seconds
                    ):

                        raise MetadataAcquisitionError(
                            "DURATION_LIMIT_EXCEEDED",
                            "Video exceeds duration limit.",
                            False,
                        )

                    return {
                        "id": info.get(
                            "id"
                        ),
                        "title": (
                            info.get(
                                "title"
                            )
                            or "Unknown"
                        ),
                        "duration_seconds": duration,
                        "thumbnail": info.get(
                            "thumbnail"
                        ),
                        "channel_name": info.get(
                            "uploader"
                        ),
                        "channel_id": info.get(
                            "uploader_id"
                        ),
                        "webpage_url": info.get(
                            "webpage_url"
                        ),
                        "upload_date": info.get(
                            "upload_date"
                        ),
                        "live_status": info.get(
                            "live_status"
                        ),
                        "availability": info.get(
                            "availability"
                        ),
                    }

            except MetadataAcquisitionError:
                raise

            except DownloadError as exc:

                code, retryable = (
                    cls._classify_error(
                        exc
                    )
                )

                raise MetadataAcquisitionError(
                    code,
                    str(exc)[:1000],
                    retryable,
                ) from exc

            except Exception as exc:

                raise MetadataAcquisitionError(
                    "METADATA_FAILED",
                    f"{type(exc).__name__}: {exc}",
                    True,
                ) from exc

        return await asyncio.to_thread(
            _fetch
        )

    @classmethod
    def _build_options(
        cls,
        *,
        player_clients: tuple[str, ...] | None,
        cookie_file: str | None,
    ) -> dict[str, Any]:

        clients = (
            player_clients
            or cls.DEFAULT_PLAYER_CLIENTS
        )

        options: dict[str, Any] = {
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "ignoreerrors": False,
            "ignore_no_formats_error": True,

            "extractor_args": {
                "youtube": {
                    "player_client": list(
                        clients
                    ),
                }
            },
        }

        if cookie_file:

            if not os.path.isfile(
                cookie_file
            ):

                raise MetadataAcquisitionError(
                    "COOKIE_FILE_NOT_FOUND",
                    "Configured cookie file does not exist.",
                    False,
                )

            options["cookiefile"] = (
                cookie_file
            )

        return options

    @staticmethod
    def _classify_error(
        exc: DownloadError,
    ) -> tuple[str, bool]:

        message = str(
            exc
        ).casefold()

        if (
            "private video"
            in message
        ):
            return (
                "ACCESS_DENIED",
                False,
            )

        if (
            "sign in"
            in message
            or "login"
            in message
        ):
            return (
                "AUTH_REQUIRED",
                False,
            )

        if (
            "not available"
            in message
            or "video unavailable"
            in message
        ):
            return (
                "VIDEO_NOT_FOUND",
                False,
            )

        if (
            "429"
            in message
            or "too many requests"
            in message
        ):
            return (
                "RATE_LIMITED",
                True,
            )

        if (
            "timeout"
            in message
            or "timed out"
            in message
        ):
            return (
                "NETWORK_TIMEOUT",
                True,
            )

        return (
            "METADATA_FAILED",
            True,
        )
