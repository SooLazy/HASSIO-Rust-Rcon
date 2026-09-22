"""Tests for RustRconClient against a fake WebRCON server."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest
from aiohttp import WSMsgType, web
from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "rust_rcon"))

from rcon import RustRconAuthError, RustRconClient, RustRconError  # noqa: E402

PASSWORD = "hunter2"


def _password_from_path(request: web.Request) -> str:
    return unquote(request.path.lstrip("/"))


async def _echo_handler(request: web.Request) -> web.WebSocketResponse:
    """Reply to any command with a canned response carrying the same Identifier."""
    if _password_from_path(request) != PASSWORD:
        # Real servers just close the socket on bad auth, without replying.
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.close()
        return ws

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)
            await ws.send_json(
                {"Identifier": data["Identifier"], "Message": f"echo:{data['Message']}"}
            )
    return ws


async def _hang_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await asyncio.sleep(3600)
    return ws


@pytest.fixture
async def make_client():
    servers: list[TestServer] = []
    clients: list[TestClient] = []

    async def _make(handler):
        app = web.Application()
        app.router.add_route("GET", "/{password}", handler)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()
        servers.append(server)
        clients.append(client)
        host = client.host
        port = client.port
        return RustRconClient(client.session, host, port, PASSWORD)

    yield _make

    for client in clients:
        await client.close()


async def test_successful_command_returns_message(make_client) -> None:
    client = await make_client(_echo_handler)
    result = await client.async_command("serverinfo")
    assert result == "echo:serverinfo"


async def test_bad_password_raises_auth_error(make_client) -> None:
    app = web.Application()
    app.router.add_route("GET", "/{password}", _echo_handler)
    server = TestServer(app)
    test_client = TestClient(server)
    await test_client.start_server()
    try:
        client = RustRconClient(
            test_client.session, test_client.host, test_client.port, "wrong-password"
        )
        with pytest.raises(RustRconAuthError):
            await client.async_command("serverinfo", retries=1)
    finally:
        await test_client.close()


async def test_timeout_is_retried_then_raises(make_client) -> None:
    client = await make_client(_hang_handler)
    with pytest.raises(RustRconError):
        await client.async_command("serverinfo", timeout=0.05, retries=2)
