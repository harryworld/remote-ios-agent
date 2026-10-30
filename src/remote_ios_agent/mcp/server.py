import asyncio
from pathlib import Path

from remote_ios_agent.api.session import AsyncRemoteIOS
from remote_ios_agent.core.config import Config
from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.models import serializable


def create_server(config: Config | None = None):
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        raise RemoteIOSError("dependency_missing", "Install remote-ios-agent[mcp]") from exc
    config = config or Config.load()
    server = MCPServer("remote-ios-agent")
    api = AsyncRemoteIOS(config)
    # The upstream userspace tunnel supports one active tunnel per process.
    gate = asyncio.Lock()

    async def with_device(device, operation, **arguments):
        try:
            async with gate:
                async with await api.session(device) as session:
                    result = await operation(session, **arguments)
                    if isinstance(result, dict):
                        if result.get("status") in {"failed", "timeout", "stopped"}:
                            raise RemoteIOSError(
                                "workflow_incomplete", result["status"], details=serializable(result)
                            )
                        if result.get("ui_changed") is False:
                            raise RemoteIOSError(
                                "no_visual_change",
                                "No UI change above threshold",
                                details=serializable(result),
                            )
                    return {"ok": True, "result": serializable(result)}
        except Exception as exc:
            error = (
                exc.as_dict()
                if isinstance(exc, RemoteIOSError)
                else {"code": "backend_error", "message": type(exc).__name__}
            )
            return {"ok": False, "error": error}

    @server.tool()
    async def ios_devices_list() -> dict:
        """List configured/discovered devices. Listing does not prove connectivity."""
        try:
            return {"ok": True, "result": serializable(await api.devices()), "connection_verified": False}
        except RemoteIOSError as exc:
            return {"ok": False, "error": exc.as_dict()}

    @server.tool()
    async def ios_device_connect(device: str | None = None) -> dict:
        """Probe identity and advertised capabilities; connection closes when the call returns."""
        return await with_device(device, lambda s: s.status())

    @server.tool()
    async def ios_build(project: str, timeout: float = 600) -> dict:
        """Build a trusted local SwiftPM/xtool project. Does not imply valid device signing."""
        from remote_ios_agent.build.runner import build

        try:
            return {"ok": True, "result": await build(project, config.artifacts, timeout)}
        except RemoteIOSError as exc:
            return {"ok": False, "error": exc.as_dict()}

    @server.tool()
    async def ios_install(path: str, device: str | None = None) -> dict:
        """Install an already signed IPA/app and verify its bundle appears in lookup."""
        return await with_device(device, lambda s: s.install(Path(path)))

    @server.tool()
    async def ios_launch(bundle_id: str, device: str | None = None) -> dict:
        return await with_device(device, lambda s: s.launch(bundle_id))

    @server.tool()
    async def ios_screenshot(device: str | None = None) -> dict:
        return await with_device(device, lambda s: s.screenshot())

    @server.tool()
    async def ios_tap(x: float, y: float, device: str | None = None) -> dict:
        """Pixel-coordinate tap. Dispatched does not mean UI verified; use ios_interact_verify."""
        return await with_device(device, lambda s: s.tap(x, y))

    @server.tool()
    async def ios_swipe(
        x1: float, y1: float, x2: float, y2: float, duration: float = 0.6, device: str | None = None
    ) -> dict:
        return await with_device(device, lambda s: s.swipe((x1, y1), (x2, y2), duration))

    @server.tool()
    async def ios_type_text(text: str, device: str | None = None) -> dict:
        """Native US ASCII HID input; focused field and UI verification are caller responsibilities."""
        return await with_device(device, lambda s: s.type_text(text))

    @server.tool()
    async def ios_get_ui_tree(device: str | None = None) -> dict:
        """Optional: requires a provisioned, running WDA session."""
        from remote_ios_agent.automation.wda import WDA

        return await with_device(device, lambda s: WDA(s.device.wda_url, s.device.wda_session).tree())

    @server.tool()
    async def ios_record_video(seconds: float = 5, interval: float = 1, device: str | None = None) -> dict:
        """Sampled screenshot video using FFmpeg, not native realtime HEVC; audio unavailable."""
        from remote_ios_agent.capture.video import record

        return await with_device(device, lambda s: record(s, seconds, interval))

    @server.tool()
    async def ios_get_logs(bundle_id: str, seconds: float = 5, device: str | None = None) -> dict:
        return await with_device(device, lambda s: s.logs(bundle_id, seconds))

    @server.tool()
    async def ios_interact_verify(
        x: float, y: float, device: str | None = None, roi: list[int] | None = None, threshold: float = 0.01
    ) -> dict:
        """Before/tap/after in one session. Pixel change is evidence, not proof of causality."""
        from remote_ios_agent.workflows.runner import interact_verify

        return await with_device(device, lambda s: interact_verify(s, x, y, roi=roi, threshold=threshold))

    @server.tool()
    async def ios_run_workflow(
        steps: list[dict], device: str | None = None, max_actions: int = 20, timeout: float = 120
    ) -> dict:
        """Run bounded, observable steps in one device session. Inspect report.status and each step."""
        from remote_ios_agent.workflows.runner import execute

        return await with_device(
            device, lambda s: execute(s, steps, max_actions=max_actions, timeout=timeout)
        )

    @server.tool()
    async def ios_app_get_state() -> dict:
        """Reserved SDK capability; unavailable until authenticated app broker is implemented."""
        return {
            "ok": False,
            "error": unsupported("sdk_state", "App transport/broker is a later milestone").as_dict(),
        }

    @server.tool()
    async def ios_app_perform_action(name: str, arguments: dict | None = None) -> dict:
        return {
            "ok": False,
            "error": unsupported("sdk_actions", "App transport/broker is a later milestone").as_dict(),
        }

    @server.tool()
    async def ios_feedback_list() -> dict:
        return {
            "ok": False,
            "error": unsupported("feedback", "Feedback ingestion is a later milestone").as_dict(),
        }

    @server.tool()
    async def ios_feedback_get(identifier: str) -> dict:
        return {
            "ok": False,
            "error": unsupported("feedback", "Feedback ingestion is a later milestone").as_dict(),
        }

    return server


def main():
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
