"""Bounded, auditable subprocess execution for audio normalization."""

import logging
import subprocess
import threading

from .config import settings
from .storage import delete_file

logger = logging.getLogger("mobile_money_corpus_manager")
CONVERSION_SLOTS = threading.BoundedSemaphore(settings.max_concurrent_conversions)


class ConversionSaturated(Exception):
    """Raised when all FFmpeg conversion slots are occupied."""


def run_audio_command(args, *, slots=CONVERSION_SLOTS, **kwargs):
    """Run FFmpeg/ffprobe without a shell and with bounded concurrency."""
    if not slots.acquire(blocking=False):
        raise ConversionSaturated()
    try:
        return subprocess.run(args, shell=False, **kwargs)
    finally:
        slots.release()


def operation_id(request):
    return request.headers.get("x-request-id") or __import__("uuid").uuid4().hex


def audio_error(request, status_code, message):
    from fastapi import HTTPException

    op = operation_id(request)
    logger.warning("audio operation failed", extra={"operation_id": op, "status_code": status_code})
    return HTTPException(status_code, message, headers={"X-Operation-ID": op})


def compensate_uploaded(uploaded, request, *, delete=delete_file):
    for object_name in uploaded:
        try:
            delete(object_name)
        except Exception:
            logger.error(
                "MinIO compensation failed; reconciliation required",
                extra={"operation_id": operation_id(request)},
            )
