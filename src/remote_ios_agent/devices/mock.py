import asyncio
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.models import Capability, DeviceInfo


class MockBackend:
    """Explicit simulation. Never selected as a fallback for real hardware failures."""

    simulated = True

    def __init__(self, config):
        self.config = config
        self.count = 0
        self.app = None
        self.installed = set()
        self.connected = False

    async def connect(self):
        self.connected = True
        return DeviceInfo(self.config.identifier, "SIMULATED iPhone", "mock", "mock", True)

    async def disconnect(self):
        self.connected = False

    def capabilities(self):
        return {
            name: Capability(True, "SIMULATION ONLY", "mock")
            for name in (
                "screenshot",
                "tap",
                "swipe",
                "long_press",
                "type_text",
                "press",
                "install",
                "launch",
                "logs",
            )
        }

    async def screenshot(self):
        image = Image.new("RGB", (390, 844), "#14283f")
        draw = ImageDraw.Draw(image)
        draw.text((20, 40), "SIMULATED DEVICE - NO HARDWARE", fill="white")
        draw.rectangle((80, 300, 310, 450), fill="#29ad92" if self.count % 2 else "#436fb0")
        draw.text((110, 350), f"Button count: {self.count}", fill="white")
        result = BytesIO()
        image.save(result, format="PNG")
        return result.getvalue()

    @asynccontextmanager
    async def interaction(self):
        yield

    async def touch(self, x, y, *, end=None, duration=0.05):
        if 80 / 390 <= x / 65535 <= 310 / 390 and 300 / 844 <= y / 65535 <= 450 / 844:
            self.count += 1

    async def type_text(self, text):
        self.count += 1

    async def press(self, button):
        if button not in {"home", "lock", "volume-up", "volume-down", "mute"}:
            raise unsupported(button, "unknown hardware button")
        self.count += 1

    async def install(self, path: Path):
        if not path.exists():
            raise RemoteIOSError("artifact_missing", str(path))
        return {"status": "simulated_install", "simulated": True}

    async def launch(self, bundle_id):
        self.app = bundle_id
        return {"pid": 123, "bundle_id": bundle_id, "simulated": True}

    async def terminate(self, bundle_id):
        self.app = None
        return {"status": "simulated_termination", "simulated": True}

    async def logs(self, bundle_id):
        yield f"SIMULATED {bundle_id}: mock log"
        await asyncio.sleep(3600)
