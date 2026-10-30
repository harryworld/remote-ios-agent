import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from remote_ios_agent.core.errors import RemoteIOSError, unsupported


class WDA:
    """Optional client for an already provisioned/running WDA; never installs XCTest implicitly."""

    def __init__(self, url: str | None, session: str | None, timeout: float = 10):
        if not url or not session:
            raise unsupported("wda", "Configure wda_url and an existing wda_session for the selected device")
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
            raise RemoteIOSError("configuration_error", "WDA URL must be http(s), without inline credentials")
        self.base = url.rstrip("/") + "/session/" + quote(session, safe="")
        self.timeout = timeout

    async def request(self, path, body=None):
        def fetch():
            request = Request(
                self.base + path,
                data=json.dumps(body).encode() if body is not None else None,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    result = json.load(response)
            except (HTTPError, URLError) as exc:
                raise RemoteIOSError("wda_transport", type(exc).__name__) from exc
            value = result.get("value")
            if isinstance(value, dict) and value.get("error"):
                raise RemoteIOSError("wda_error", str(value["error"]))
            return value

        return await asyncio.to_thread(fetch)

    async def tree(self):
        return await self.request("/source")

    async def find(self, identifier):
        value = await self.request("/element", {"using": "accessibility id", "value": identifier})
        element = value.get("element-6066-11e4-a52e-4f735466cecf") or value.get("ELEMENT")
        if not element:
            raise RemoteIOSError("wda_error", "No element identifier in WDA response")
        return element

    async def tap(self, identifier):
        element = await self.find(identifier)
        await self.request(f"/element/{quote(element, safe='')}/click", {})
        return {"status": "dispatched", "verified": False, "identifier": identifier}

    async def wait(self, identifier, timeout=10):
        if not 0 < timeout <= 60:
            raise RemoteIOSError("invalid_argument", "wait timeout must be (0,60]")
        try:
            async with asyncio.timeout(timeout):
                while True:
                    try:
                        element = await self.find(identifier)
                        visible = await self.request(f"/element/{quote(element, safe='')}/displayed")
                        if visible is True:
                            return {"identifier": identifier, "visible": True, "verified_by": "wda_displayed"}
                    except RemoteIOSError as exc:
                        if exc.code != "wda_error" or str(exc) != "no such element":
                            raise
                    await asyncio.sleep(0.25)
        except TimeoutError as exc:
            raise RemoteIOSError(
                "condition_timeout", "Element did not become visible before deadline"
            ) from exc
