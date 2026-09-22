"""Tests for the pure WebRCON reply parsers."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "rust_rcon"))

from parsers import parse_playerlist, parse_serverinfo  # noqa: E402


def test_parse_serverinfo_extracts_json_object() -> None:
    raw = 'some log noise\n{"Hostname": "My Server", "Players": 5, "MaxPlayers": 100}\ntrailing'
    info = parse_serverinfo(raw)
    assert info == {"Hostname": "My Server", "Players": 5, "MaxPlayers": 100}


def test_parse_serverinfo_raises_without_json() -> None:
    with pytest.raises(ValueError):
        parse_serverinfo("no json here")


def test_parse_serverinfo_raises_on_malformed_json() -> None:
    with pytest.raises(ValueError):
        parse_serverinfo("{not valid json}")


def test_parse_playerlist_extracts_array() -> None:
    raw = '[{"SteamID": "1", "DisplayName": "Alice"}, {"SteamID": "2", "DisplayName": "Bob"}]'
    players = parse_playerlist(raw)
    assert players == [
        {"SteamID": "1", "DisplayName": "Alice"},
        {"SteamID": "2", "DisplayName": "Bob"},
    ]


def test_parse_playerlist_empty_array() -> None:
    assert parse_playerlist("[]") == []


def test_parse_playerlist_returns_empty_list_when_no_array() -> None:
    assert parse_playerlist("Unknown command") == []


def test_parse_playerlist_returns_empty_list_on_malformed_json() -> None:
    assert parse_playerlist("[not valid") == []
