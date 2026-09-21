"""Minimal WebRCON client for Rust."""
from __future__ import annotations

import asyncio
import json
import logging
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

    async def async_command(
        self, command: str, timeout: float = 15, retries: int = 2
    ) -> str:
        """Run a command, retrying on timeouts and connection errors."""
        last: RustRconError | None = None
        for attempt in range(1, retries + 1):
            try:
                return await self._async_command_once(command, timeout)
            except RustRconAuthError:
                raise
            except RustRconError as err:
                last = err
                _LOGGER.debug("RCON attempt %s/%s failed: %s", attempt, retries, err)
                await asyncio.sleep(1)
        assert last is not None
        raise last

    async def _async_command_once(self, command: str, timeout: float) -> str:
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
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                except ValueError:
                                    continue
                                reply_id = data.get("Identifier")
                                text = data.get("Message", "") or ""
                                _LOGGER.debug(
                                    "RCON reply id=%r (sent %s)", reply_id, identifier
                                )
                                if reply_id == identifier:
                                    return text
                                # Fallbacks for setups that answer with another id.
                                if command == "serverinfo" and text.lstrip().startswith("{"):
                                    return text
                                if reply_id not in (0, -1, None) and command != "serverinfo":
                                    return text
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
