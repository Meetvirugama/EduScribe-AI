from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ExportError


class Exporter:

    @classmethod
    def export_all(
        cls,
        canonical_segments: list[
            dict[str, Any]
        ],
        metadata: dict[str, Any],
        output_dir: str,
        *,
        include_timestamped_txt: bool = True,
    ) -> dict[str, dict[str, Any]]:

        cls._validate_segments(
            canonical_segments
        )

        output = Path(
            output_dir
        )

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifacts = {}

        targets = [
            (
                "txt",
                output
                / "transcript.txt",
                cls.export_txt,
            ),
            (
                "srt",
                output
                / "transcript.srt",
                cls.export_srt,
            ),
            (
                "vtt",
                output
                / "transcript.vtt",
                cls.export_vtt,
            ),
            (
                "json",
                output
                / "transcript.json",
                cls.export_json,
            ),
        ]

        if include_timestamped_txt:

            targets.append(
                (
                    "txt_timestamped",
                    output
                    / "transcript_timestamped.txt",
                    cls.export_timestamped_txt,
                )
            )

        json_data = {
            "metadata": metadata,
            "segments": canonical_segments,
        }

        for (
            artifact_type,
            path,
            function,
        ) in targets:

            if artifact_type == "json":

                function(
                    json_data,
                    str(path),
                )

            else:

                function(
                    canonical_segments,
                    str(path),
                )

            if not path.is_file():

                raise ExportError(
                    f"Artifact was not created: {path}"
                )

            artifacts[
                artifact_type
            ] = cls._artifact_metadata(
                path
            )

        return artifacts

    @classmethod
    def export_txt(
        cls,
        segments: list[
            dict[str, Any]
        ],
        output_path: str,
    ) -> None:

        lines = [
            str(
                segment["text"]
            ).strip()
            for segment in segments
            if str(
                segment.get("text")
                or ""
            ).strip()
        ]

        content = (
            "\n".join(lines)
            + ("\n" if lines else "")
        )

        cls._atomic_write(
            output_path,
            content,
        )

    @classmethod
    def export_timestamped_txt(
        cls,
        segments: list[
            dict[str, Any]
        ],
        output_path: str,
    ) -> None:

        lines = []

        for segment in segments:

            timestamp = (
                cls._format_timestamp(
                    float(
                        segment["start"]
                    ),
                    "txt",
                )
            )

            lines.append(
                f"{timestamp} "
                f"{segment['text']}"
            )

        content = (
            "\n".join(lines)
            + ("\n" if lines else "")
        )

        cls._atomic_write(
            output_path,
            content,
        )

    @classmethod
    def export_srt(
        cls,
        segments: list[
            dict[str, Any]
        ],
        output_path: str,
    ) -> None:

        blocks = []

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            start = (
                cls._format_timestamp(
                    float(
                        segment["start"]
                    ),
                    "srt",
                )
            )

            end = (
                cls._format_timestamp(
                    float(
                        segment["end"]
                    ),
                    "srt",
                )
            )

            text = (
                str(
                    segment["text"]
                )
                .replace(
                    "\r",
                    "",
                )
                .strip()
            )

            blocks.append(
                f"{index}\n"
                f"{start} --> {end}\n"
                f"{text}"
            )

        content = (
            "\n\n".join(
                blocks
            )
            + (
                "\n\n"
                if blocks
                else ""
            )
        )

        cls._atomic_write(
            output_path,
            content,
        )

    @classmethod
    def export_vtt(
        cls,
        segments: list[
            dict[str, Any]
        ],
        output_path: str,
    ) -> None:

        lines = [
            "WEBVTT",
            "",
        ]

        for segment in segments:

            start = (
                cls._format_timestamp(
                    float(
                        segment["start"]
                    ),
                    "vtt",
                )
            )

            end = (
                cls._format_timestamp(
                    float(
                        segment["end"]
                    ),
                    "vtt",
                )
            )

            text = (
                str(
                    segment["text"]
                )
                .replace(
                    "\r",
                    "",
                )
                .strip()
            )

            lines.extend(
                [
                    f"{start} --> {end}",
                    text,
                    "",
                ]
            )

        content = (
            "\n".join(
                lines
            ).rstrip()
            + "\n"
        )

        cls._atomic_write(
            output_path,
            content,
        )

    @classmethod
    def export_json(
        cls,
        data: dict[str, Any],
        output_path: str,
    ) -> None:

        try:

            content = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ExportError(
                f"JSON serialization failed: {exc}"
            ) from exc

        cls._atomic_write(
            output_path,
            content + "\n",
        )

    @classmethod
    def _validate_segments(
        cls,
        segments: list[
            dict[str, Any]
        ],
    ) -> None:

        if not segments:

            raise ExportError(
                "Cannot export empty transcript."
            )

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            try:

                start = float(
                    segment["start"]
                )

                end = float(
                    segment["end"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ) as exc:

                raise ExportError(
                    f"Invalid timestamps in segment {index}."
                ) from exc

            if (
                not math.isfinite(start)
                or not math.isfinite(end)
            ):

                raise ExportError(
                    f"Non-finite timestamps in segment {index}."
                )

            if (
                start < 0
                or end <= start
            ):

                raise ExportError(
                    f"Invalid time interval in segment {index}."
                )

            if not str(
                segment.get("text")
                or ""
            ).strip():

                raise ExportError(
                    f"Empty text in segment {index}."
                )

    @staticmethod
    def _format_timestamp(
        seconds: float,
        format_type: str,
    ) -> str:

        if (
            not math.isfinite(
                seconds
            )
            or seconds < 0
        ):

            raise ExportError(
                "Timestamp must be finite and non-negative."
            )

        total_ms = int(
            round(
                seconds * 1000
            )
        )

        hours, remainder = divmod(
            total_ms,
            3_600_000,
        )

        minutes, remainder = divmod(
            remainder,
            60_000,
        )

        secs, milliseconds = divmod(
            remainder,
            1000,
        )

        if format_type == "srt":

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d},"
                f"{milliseconds:03d}"
            )

        if format_type == "vtt":

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}."
                f"{milliseconds:03d}"
            )

        if format_type == "txt":

            return (
                f"[{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}]"
            )

        raise ExportError(
            f"Unsupported timestamp format: {format_type}"
        )

    @classmethod
    def _atomic_write(
        cls,
        output_path: str,
        content: str,
    ) -> None:

        path = Path(
            output_path
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fd, temp_name = (
            tempfile.mkstemp(
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=str(
                    path.parent
                ),
                text=True,
            )
        )

        try:

            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as file:

                file.write(
                    content
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )

            os.replace(
                temp_name,
                path,
            )

        except Exception as exc:

            try:
                os.unlink(
                    temp_name
                )
            except OSError:
                pass

            raise ExportError(
                f"Atomic export failed: {exc}"
            ) from exc

    @staticmethod
    def _artifact_metadata(
        path: Path,
    ) -> dict[str, Any]:

        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:

            for chunk in iter(
                lambda: file.read(
                    1024 * 1024
                ),
                b"",
            ):

                digest.update(
                    chunk
                )

        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": digest.hexdigest(),
            "status": "READY",
        }
