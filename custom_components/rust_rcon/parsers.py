"""Pure parsing helpers for WebRCON replies.

Kept free of any Home Assistant imports so they can be unit tested without
the full HA test harness.
"""
from __future__ import annotations

import json
from typing import Any


def parse_serverinfo(raw: str) -> dict[str, Any]:
    """Extract the JSON object from a `serverinfo` reply."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON in serverinfo reply")
    return json.loads(raw[start : end + 1])


def parse_playerlist(raw: str) -> list[dict[str, Any]]:
    """Extract the JSON array from a `playerlist` reply.

    Returns an empty list if the reply doesn't contain a JSON array
    (e.g. an empty server, or a plugin that changed the output).
    """
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(raw[start : end + 1])
    except ValueError:
        return []
    return data if isinstance(data, list) else []
