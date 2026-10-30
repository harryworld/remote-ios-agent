"""Adapter contract tests against the pinned library. No physical device is involved."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from remote_ios_agent.core.config import DeviceConfig
from remote_ios_agent.core.errors import RemoteIOSError
from remote_ios_agent.devices.pmd3 import PMD3Backend

pmd = pytest.importorskip("pymobiledevice3")


def test_pinned_api_contract():
    from pymobiledevice3.remote.core_device.display_service import DisplayService
    from pymobiledevice3.remote.core_device.hid_service import UniversalHIDServiceService, touch_session
    from pymobiledevice3.remote.core_device.screen_capture_service import ScreenCaptureService
    from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl

    assert callable(touch_session)
    assert hasattr(UniversalHIDServiceService, "send_touchscreen")
    assert hasattr(ScreenCaptureService, "capture_screenshot")
    assert hasattr(ProcessControl, "process_identifier_for_bundle_identifier")
    assert DisplayService.SERVICE_NAME == "com.apple.coredevice.displayservice"


async def test_hid_auth_context_is_used_and_released(monkeypatch):
    from pymobiledevice3.remote.core_device import hid_service

    entered, exited = [], []
    hid = SimpleNamespace(send_touchscreen=AsyncMock())

    @asynccontextmanager
    async def auth(rsd):
        entered.append(True)
        try:
            yield hid
        finally:
            exited.append(True)

    monkeypatch.setattr(hid_service, "touch_session", auth)
    backend = PMD3Backend(DeviceConfig("phone", "id"))
    await backend.touch(100, 200, end=(300, 400), duration=0.01)
    assert entered == exited == [True]
    calls = hid.send_touchscreen.call_args_list
    assert calls[0].args == (hid_service.TOUCHSCREEN_STATE_CONTACT, 100, 200)
    assert calls[-1].args == (hid_service.TOUCHSCREEN_STATE_RELEASE, 300, 400)
    assert backend.hid is None


async def test_cancellation_releases_contact():
    from pymobiledevice3.remote.core_device.hid_service import TOUCHSCREEN_STATE_RELEASE

    backend = PMD3Backend(DeviceConfig("phone", "id"))
    backend.hid = SimpleNamespace(send_touchscreen=AsyncMock())
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.01):
            await backend.touch(100, 200, end=None, duration=10)
    assert backend.hid.send_touchscreen.call_args_list[-1].args == (TOUCHSCREEN_STATE_RELEASE, 100, 200)


async def test_unicode_rejected_before_partial_input():
    backend = PMD3Backend(DeviceConfig("phone", "id"))
    with pytest.raises(RemoteIOSError) as error:
        await backend.type_text("Hello 世界")
    assert error.value.code == "capability_unavailable"


async def test_session_reuses_hid(monkeypatch):
    from pymobiledevice3.remote.core_device import hid_service

    opens = []

    @asynccontextmanager
    async def auth(rsd):
        opens.append(True)
        yield SimpleNamespace(send_touchscreen=AsyncMock())

    monkeypatch.setattr(hid_service, "touch_session", auth)
    backend = PMD3Backend(DeviceConfig("phone", "id"))
    async with backend.interaction():
        await backend.touch(1, 1, end=None, duration=0.01)
        await backend.touch(2, 2, end=None, duration=0.01)
    assert len(opens) == 1


def test_missing_services_report_unavailable():
    backend = PMD3Backend(DeviceConfig("phone", "id"))
    backend.rsd = SimpleNamespace(peer_info={"Services": {}})
    assert not backend.capabilities()["tap"].available
