"""
Tests for the explicit vehicle-backend guard in uavsys/drones/mavsdk_client.py.

Invariant: a px4-requested run must connect for real or raise — it must NEVER
silently fall back to mock. mock runs skip real I/O. Every client records the
requested and actual backend.

MAVSDK System is created lazily (px4 connect path only) and _connect_loop is
monkeypatched here, so these tests need no running SITL/MAVSDK server.
Run: python3 -m pytest tests/test_backend_guard.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.drones.mavsdk_client import MavsdkClient  # noqa: E402


def _client(backend, **kw):
    return MavsdkClient(grpc_port=50051, system_address="udpin://0.0.0.0:14540",
                        agent_name="Agent 1", backend=backend, **kw)


def test_invalid_backend_rejected():
    with pytest.raises(ValueError, match="Unknown vehicle backend"):
        _client("sim")


def test_mock_backend_skips_io_and_never_spawns_system():
    c = _client("mock")
    assert c.requested_backend == "mock"
    asyncio.run(c.connect())
    assert c.mock_mode is True
    assert c.actual_backend == "mock"
    assert c.drone is None            # lazy System never created in mock


def test_px4_success_sets_actual_px4(monkeypatch):
    c = _client("px4")

    async def fake_loop():
        c.is_connected = True          # simulate a healthy connect (no System/I/O)

    monkeypatch.setattr(c, "_connect_loop", fake_loop)
    asyncio.run(c.connect())
    assert c.actual_backend == "px4"
    assert c.mock_mode is False


def test_px4_connection_failure_raises_and_never_falls_back_to_mock(monkeypatch):
    c = _client("px4")

    async def boom():
        raise RuntimeError("no SITL here")

    monkeypatch.setattr(c, "_connect_loop", boom)
    with pytest.raises(RuntimeError, match="Refusing to fall back to mock"):
        asyncio.run(c.connect())
    assert c.mock_mode is False        # the whole point: never silent mock
    assert c.actual_backend is None    # not "mock"


def test_px4_timeout_raises_and_never_falls_back_to_mock(monkeypatch):
    c = _client("px4", connect_timeout=0.01)

    async def slow():
        await asyncio.sleep(1.0)       # exceeds the 0.01s timeout

    monkeypatch.setattr(c, "_connect_loop", slow)
    with pytest.raises(RuntimeError, match="timed out"):
        asyncio.run(c.connect())
    assert c.mock_mode is False
    assert c.actual_backend is None


def test_requested_backend_is_recorded():
    assert _client("px4").requested_backend == "px4"
    assert _client("mock").requested_backend == "mock"
    # Class default is the safe/inert mock (never accidental px4).
    assert MavsdkClient(50051, "udpin://0.0.0.0:14540", "Agent 1").requested_backend == "mock"
