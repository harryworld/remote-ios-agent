import asyncio
import re
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from remote_ios_agent.connectivity.pmd3 import open_rsd
from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.models import Capability, DeviceInfo
from remote_ios_agent.deployment.package import bundle_identifier


class PMD3Backend:
    simulated = False

    def __init__(self, config):
        self.config = config
        self.stack = AsyncExitStack()
        self.rsd = None
        self.hid = None
        self._dvt = None
        self._process = None

    async def connect(self):
        try:
            self.rsd = await open_rsd(self.config, self.stack)
            if self.rsd.udid != self.config.identifier:
                raise RemoteIOSError("device_mismatch", "RSD identity differs from the selected device")
            return DeviceInfo(
                self.rsd.udid, self.config.name, self.config.transport, self.rsd.product_version
            )
        except BaseException:
            await self.disconnect()
            raise

    async def disconnect(self):
        await self.stack.aclose()
        self.hid = self.rsd = self._dvt = self._process = None

    def capabilities(self):
        services = (self.rsd.peer_info or {}).get("Services", {}) if self.rsd else {}
        requirements = {
            "screenshot": ["com.apple.coredevice.screencaptureservice"],
            "tap": ["com.apple.coredevice.hid.universalhidservice", "com.apple.coredevice.displayservice"],
            "press": ["com.apple.coredevice.hid.indigo"],
            "install": ["com.apple.mobile.installation_proxy.shim.remote"],
            "logs": ["com.apple.syslog_relay.shim.remote"],
        }
        result = {}
        for name, needed in requirements.items():
            missing = [s for s in needed if s not in services]
            result[name] = Capability(
                not missing,
                "Missing services: " + ", ".join(missing)
                if missing
                else "Services advertised; execution and UI effect require verification",
                "rsd_service_advertisement",
            )
        for name in ("swipe", "long_press", "type_text"):
            result[name] = result["tap"]
        dvt = any("dtservicehub" in s for s in services)
        result["launch"] = Capability(
            dvt,
            "DVT advertisement; launch still requires a signed app and unlocked device",
            "rsd_service_advertisement",
        )
        result["native_video"] = Capability(
            False, "Native HEVC recording adapter not implemented; use sampled video"
        )
        return result

    async def screenshot(self):
        from pymobiledevice3.remote.core_device.screen_capture_service import ScreenCaptureService

        async with ScreenCaptureService(self.rsd) as service:
            result = await service.capture_screenshot()
            if not isinstance(result.get("image"), bytes):
                raise RemoteIOSError("invalid_capture", "Device did not return screenshot bytes")
            return result["image"]

    @asynccontextmanager
    async def interaction(self):
        if self.hid is not None:
            yield
            return
        from pymobiledevice3.remote.core_device.hid_service import touch_session

        async with touch_session(self.rsd) as hid:
            self.hid = hid
            try:
                yield
            finally:
                self.hid = None

    async def touch(self, x, y, *, end=None, duration=0.05):
        from pymobiledevice3.remote.core_device.hid_service import (
            TOUCHSCREEN_STATE_CONTACT,
            TOUCHSCREEN_STATE_RELEASE,
        )

        async with self.interaction():
            last = (x, y)
            try:
                steps = max(1, round(duration * 60)) if end else 1
                for index in range(steps + 1):
                    t = index / steps
                    last = (round(x + (end[0] - x) * t), round(y + (end[1] - y) * t)) if end else (x, y)
                    await self.hid.send_touchscreen(TOUCHSCREEN_STATE_CONTACT, *last)
                    if index < steps:
                        await asyncio.sleep(duration / steps)
            finally:
                # Release on timeout/cancellation too; never leave a finger down intentionally.
                await self.hid.send_touchscreen(TOUCHSCREEN_STATE_RELEASE, *last)

    async def type_text(self, text):
        from pymobiledevice3.remote.core_device.hid_service import ASCII_TO_HID, KEY_LEFT_SHIFT

        if any(ch not in ASCII_TO_HID for ch in text):
            raise unsupported(
                "type_text", "Native keyboard supports US-layout ASCII only; use SDK/WDA for Unicode"
            )
        async with self.interaction():
            keyboard = await self.hid.create_keyboard_service()
            try:
                for ch in text:
                    usage, shift = ASCII_TO_HID[ch]
                    if shift:
                        await self.hid.send_keyboard(keyboard, (KEY_LEFT_SHIFT,))
                        await asyncio.sleep(0.04)
                    await self.hid.send_keyboard(keyboard, (KEY_LEFT_SHIFT, usage) if shift else (usage,))
                    await asyncio.sleep(0.04)
                    await self.hid.send_keyboard(keyboard, ())
                    await asyncio.sleep(0.02)
            finally:
                await self.hid.send_keyboard(keyboard, ())

    async def press(self, button):
        from pymobiledevice3.remote.core_device.hid_service import IndigoHIDService

        buttons = {
            "home": (0x40, 0.05),
            "lock": (0x30, 0.5),
            "volume-up": (0xE9, 0.05),
            "volume-down": (0xEA, 0.05),
            "mute": (0xE2, 0.05),
        }
        if button not in buttons:
            raise unsupported("press", f"Unsupported button: {button}")
        code, hold = buttons[button]
        async with IndigoHIDService(self.rsd) as service:
            try:
                await service.send_button(0x0C, code, 1)
                await asyncio.sleep(hold)
            finally:
                await service.send_button(0x0C, code, 2)
            await asyncio.sleep(0.1)

    async def install(self, path: Path):
        from pymobiledevice3.services.installation_proxy import InstallationProxyService

        bundle = bundle_identifier(path)
        async with InstallationProxyService(self.rsd) as service:
            await service.install_from_local(path)
            apps = await service.get_apps()
            if bundle not in apps:
                raise RemoteIOSError(
                    "installation_unverified", "Install returned but app was absent from lookup"
                )
        return {"bundle_id": bundle, "status": "installed", "verified_by": "installation_proxy_lookup"}

    async def process(self):
        if self._process is None:
            from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
            from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl

            self._dvt = await self.stack.enter_async_context(DvtProvider(self.rsd))
            self._process = await self.stack.enter_async_context(ProcessControl(self._dvt))
        return self._process

    async def launch(self, bundle_id):
        process = await self.process()
        pid = await process.launch(bundle_id, kill_existing=False)
        actual = await process.process_identifier_for_bundle_identifier(bundle_id)
        if not actual:
            raise RemoteIOSError("launch_unverified", "App has no running PID after launch")
        return {"bundle_id": bundle_id, "pid": actual, "launch_pid": pid, "verified_by": "process_lookup"}

    async def terminate(self, bundle_id):
        process = await self.process()
        pid = await process.process_identifier_for_bundle_identifier(bundle_id)
        if not pid:
            return {"bundle_id": bundle_id, "status": "already_stopped"}
        await process.kill(pid)
        for _ in range(20):
            if not await process.process_identifier_for_bundle_identifier(bundle_id):
                return {"bundle_id": bundle_id, "status": "terminated", "verified_by": "process_lookup"}
            await asyncio.sleep(0.1)
        raise RemoteIOSError("termination_unverified", "PID still exists after termination")

    async def logs(self, bundle_id):
        from pymobiledevice3.services.syslog import SyslogService

        process = await self.process()
        pid = await process.process_identifier_for_bundle_identifier(bundle_id)
        if not pid:
            raise RemoteIOSError("app_not_running", "Launch the app before requesting PID-filtered live logs")
        pattern = re.compile(r"\[" + str(pid) + r"(?::[^\]]*)?\]")
        async with SyslogService(self.rsd) as service:
            async for line in service.watch():
                line = line.decode("utf-8", "replace") if isinstance(line, bytes) else line
                if pattern.search(line):
                    yield line
