"""
tasks.py — Backward Compatibility Shim

This file exists to provide backward compatibility for any external scripts or
imports that were looking for the background pipeline orchestrator here.
The actual implementation has moved to pipeline/orchestrator.py.
"""
import logging
from pipeline.orchestrator import process_video_pipeline_async

logger = logging.getLogger(__name__)

# Expose the same function signature as before
__all__ = ["process_video_pipeline_async"]
