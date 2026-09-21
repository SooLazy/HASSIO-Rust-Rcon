"""Minimal WebRCON client for Rust."""
from __future__ import annotations

import logging
import asyncio
import json
import random
from urllib.parse import quote

import aiohttp

_LOGGER = logging.getLogger(__name__)
class RustRconError(Exception):
    """Base error."""


class RustRconAuthError(RustRconError):
    """Connected, but the server closed the socket without answering (bad password)."""


class RustRconClient:
    """Open-per-command WebRCON client (robust against restarts and dropped sockets)."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, port: int, password: str
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._password = password
        self._lock = asyncio.Lock()

    async def async_command(self, command: str, timeout: float = 10) -> str:
        """Run a console command and return the server's response text."""
        url = f"ws://{self._host}:{self._port}/{quote(self._password, safe='')}"
        identifier = random.randint(1000, 2_000_000_000)

        async with self._lock:
            stage = "connecting"
            try:
                async with asyncio.timeout(timeout):
                    async with self._session.ws_connect(url, heartbeat=None) as ws:
                        stage = "waiting for reply"
                        await ws.send_json(
                            {
                                "Identifier": identifier,
                                "Message": command,
                                "Name": "HomeAssistant",
                            }
                        )
                        async for msg in ws:
                            _LOGGER.warning("RCON msg: %s %s", msg.type, str(msg.data)[:200])
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                except ValueError:
                                    continue
                                if data.get("Identifier") == identifier:
                                    return data.get("Message", "") or ""
                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSE,
                                aiohttp.WSMsgType.CLOSING,
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            ):
                                break
            except TimeoutError as err:
                raise RustRconError(f"Timed out while {stage}") from err
            except aiohttp.ClientError as err:
                raise RustRconError(f"Connection failed: {err}") from err

        raise RustRconAuthError(
            "Server closed the connection without replying (check the RCON password)"
        )
