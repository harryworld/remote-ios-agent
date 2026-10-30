import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from remote_ios_agent.automation.coordinates import normalize
from remote_ios_agent.capture.artifacts import save_capture
from remote_ios_agent.core.config import Config, DeviceConfig
from remote_ios_agent.core.errors import RemoteIOSError
from remote_ios_agent.core.models import ActionResult, serializable
from remote_ios_agent.devices.base import Backend


class DeviceSession:
    def __init__(self, config: Config, device: DeviceConfig, backend: Backend):
        self.config, self.device, self.backend = config, device, backend
        self.id = uuid.uuid4().hex
        self.app = None
        self.info = None
        self.ui = self
        self.lock = asyncio.Lock()

    async def call(self, operation, *args, **kwargs):
        try:
            async with asyncio.timeout(self.config.timeout):
                return await operation(*args, **kwargs)
        except RemoteIOSError:
            raise
        except TimeoutError as exc:
            raise RemoteIOSError(
                "timeout",
                "Operation deadline exceeded; effect may be unknown. Observe before retrying.",
                retryable=False,
            ) from exc
        except Exception as exc:
            # Do not expose exception bodies that may contain pairing material.
            raise RemoteIOSError(
                "backend_error",
                type(exc).__name__,
                details={"operation": operation.__name__},
                retryable=False,
            ) from exc

    async def __aenter__(self):
        self.info = await self.call(self.backend.connect)
        return self

    async def __aexit__(self, *exc):
        try:
            async with asyncio.timeout(10):
                await self.backend.disconnect()
        finally:
            self.info = None

    async def status(self):
        return {
            "device": serializable(self.info),
            "session_id": self.id,
            "capabilities": serializable(self.backend.capabilities()),
            "connection_scope": "current_process",
            "simulated": self.backend.simulated,
        }

    @asynccontextmanager
    async def interaction(self):
        # Entire bounded workflow owns this session; callers must not share it concurrently.
        async with asyncio.timeout(self.config.timeout):
            async with self.backend.interaction():
                yield self

    async def screenshot(self, action_id=None):
        async with self.lock:
            data = await self.call(self.backend.screenshot)
        return save_capture(
            data,
            self.config.artifacts / self.id,
            device=self.device.identifier,
            session_id=self.id,
            action_id=action_id,
            application_identifier=self.app,
            orientation=self.device.orientation,
            simulated=self.backend.simulated,
        )

    async def observe(self):
        return {"capture": serializable(await self.screenshot()), "status": await self.status()}

    async def _touch(self, operation, x, y, end=None, duration=0.05):
        if not 0.01 <= duration <= 10:
            raise RemoteIOSError("invalid_argument", "duration must be .01..10 seconds")
        current = await self.screenshot()
        landscape = self.device.orientation.startswith("landscape")
        if (current.width > current.height) != landscape:
            raise RemoteIOSError(
                "orientation_mismatch", "Screenshot dimensions disagree with configured orientation"
            )
        start = normalize(x, y, current.width, current.height, self.device.orientation)
        target = normalize(*end, current.width, current.height, self.device.orientation) if end else None
        async with self.lock:
            await self.call(self.backend.touch, *start, end=target, duration=duration)
        return ActionResult(uuid.uuid4().hex, self.id, operation, simulated=self.backend.simulated)

    async def tap(self, x: float, y: float):
        return await self._touch("tap", x, y)

    async def swipe(self, start: tuple[float, float], end: tuple[float, float], duration=0.6):
        return await self._touch("swipe", *start, end=end, duration=duration)

    async def long_press(self, x: float, y: float, duration=1.0):
        return await self._touch("long_press", x, y, duration=duration)

    async def type_text(self, text: str):
        if len(text) > 4096:
            raise RemoteIOSError("invalid_argument", "Text limited to 4096 characters")
        async with self.lock:
            await self.call(self.backend.type_text, text)
        return ActionResult(uuid.uuid4().hex, self.id, "type_text", simulated=self.backend.simulated)

    async def press(self, button: str):
        async with self.lock:
            await self.call(self.backend.press, button)
        return ActionResult(uuid.uuid4().hex, self.id, "press", simulated=self.backend.simulated)

    async def install(self, path: str | Path):
        async with self.lock:
            return await self.call(self.backend.install, Path(path).resolve())

    async def launch(self, bundle_id: str):
        async with self.lock:
            result = await self.call(self.backend.launch, bundle_id)
            self.app = bundle_id
            return result

    async def terminate(self, bundle_id: str):
        async with self.lock:
            result = await self.call(self.backend.terminate, bundle_id)
            if self.app == bundle_id:
                self.app = None
            return result

    async def logs(self, bundle_id: str, seconds: float = 5, limit: int = 200):
        if not 0 < seconds <= 60 or not 1 <= limit <= 10000:
            raise RemoteIOSError("invalid_argument", "logs require seconds in (0,60] and limit in 1..10000")
        lines = []
        iterator = self.backend.logs(bundle_id)
        try:
            async with asyncio.timeout(min(seconds, self.config.timeout)):
                async for line in iterator:
                    lines.append(line)
                    if len(lines) >= limit:
                        break
        except TimeoutError:
            pass  # Deliberate observation window, not a success claim about log availability.
        finally:
            await iterator.aclose()
        return {
            "lines": lines,
            "count": len(lines),
            "bundle_id": bundle_id,
            "window_seconds": seconds,
            "filter": "process_id_at_start",
            "simulated": self.backend.simulated,
            "note": "Live syslog only; no historical log recovery. Empty is not proof of no errors.",
        }


class AsyncRemoteIOS:
    def __init__(self, config: Config | None = None):
        self.config = config or Config.load()

    async def devices(self) -> list[DeviceConfig]:
        if self.config.backend == "mock":
            return list(self.config.devices) or [DeviceConfig("mock", "mock-iphone", "mock")]
        if self.config.devices:
            return list(self.config.devices)
        from remote_ios_agent.connectivity.pmd3 import discover_usb

        try:
            async with asyncio.timeout(self.config.timeout):
                return await discover_usb()
        except ImportError as exc:
            raise RemoteIOSError("dependency_missing", "Install remote-ios-agent[device]") from exc
        except TimeoutError as exc:
            raise RemoteIOSError("timeout", "Device discovery timed out") from exc

    async def session(self, device: str | None = None) -> DeviceSession:
        chosen = self.config.choose(await self.devices(), device)
        if self.config.backend == "mock":
            from remote_ios_agent.devices.mock import MockBackend

            backend = MockBackend(chosen)
        else:
            from remote_ios_agent.devices.pmd3 import PMD3Backend

            backend = PMD3Backend(chosen)
        return DeviceSession(self.config, chosen, backend)
