"""Trace compression utilities for efficient storage."""

import gzip
import json
from typing import Any


def compress_trace(trace_data: dict[str, Any]) -> str:
    """Compress trace data using gzip for storage.

    Args:
        trace_data: The trace dictionary to compress

    Returns:
        Compressed string representation
    """
    json_str = json.dumps(trace_data, separators=(',', ':'))
    compressed = gzip.compress(json_str.encode('utf-8'))
    return compressed.hex()


def decompress_trace(compressed_str: str) -> dict[str, Any]:
    """Decompress trace data from storage.

    Args:
        compressed_str: The compressed hex string

    Returns:
        Decompressed trace dictionary
    """
    if not compressed_str:
        return {}

    try:
        compressed_bytes = bytes.fromhex(compressed_str)
        decompressed = gzip.decompress(compressed_bytes)
        return json.loads(decompressed.decode('utf-8'))
    except (ValueError, json.JSONDecodeError, gzip.BadGzipFile):
        # If decompression fails, assume it's uncompressed JSON
        return json.loads(compressed_str)


def is_compressed(data: str) -> bool:
    """Check if data appears to be compressed.

    Args:
        data: String to check

    Returns:
        True if data appears to be compressed hex
    """
    if not data:
        return False

    # Compressed data is hex (only 0-9, a-f)
    try:
        bytes.fromhex(data[:20])
        return len(data) > 100  # Compressed data is typically longer
    except ValueError:
        return False
