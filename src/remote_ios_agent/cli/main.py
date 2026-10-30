import argparse
import asyncio
import json
import sys
from dataclasses import replace
from pathlib import Path

from remote_ios_agent.api.session import AsyncRemoteIOS
from remote_ios_agent.build.runner import build, doctor, sign
from remote_ios_agent.capture.artifacts import compare
from remote_ios_agent.core.config import Config
from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.models import serializable
from remote_ios_agent.deployment.package import package_ipa
from remote_ios_agent.workflows.runner import execute, interact_verify


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise RemoteIOSError("invalid_arguments", message)


def numbers(value, count, convert=float):
    try:
        parts = tuple(convert(item) for item in value.split(","))
        if len(parts) != count:
            raise ValueError()
        return parts
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected {count} comma-separated numbers") from exc


def parser():
    root = Parser(prog="remote-ios", description="Linux-first physical iPhone tooling. All results are JSON.")
    root.add_argument("--config")
    root.add_argument("--device", help="Explicit configured name or UDID")
    root.add_argument("--backend", choices=["pmd3", "mock"])
    root.add_argument("--artifacts")
    root.add_argument("--timeout", type=float)
    root.add_argument(
        "--orientation", choices=["portrait", "portrait-upside-down", "landscape-left", "landscape-right"]
    )
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    devices = sub.add_parser("devices").add_subparsers(dest="operation", required=True)
    devices.add_parser("list")
    devices.add_parser("info")
    device = sub.add_parser("device").add_subparsers(dest="operation", required=True)
    connection = device.add_parser("connect")
    connection.add_argument(
        "--hold", type=float, default=0, help="Keep this process's connection open, <=3600 seconds"
    )
    device.add_parser("status")
    device.add_parser("disconnect")
    builder = sub.add_parser("build")
    builder.add_argument("project", nargs="?", default=".")
    builder.add_argument("--configuration", choices=["debug", "release"], default="debug")
    builder.add_argument("--build-timeout", type=float, default=600)
    package = sub.add_parser("package")
    package.add_argument("app", type=Path)
    package.add_argument("--output", required=True, type=Path)
    signer = sub.add_parser("sign")
    signer.add_argument("app", type=Path)
    for option in ("key", "profile", "output"):
        signer.add_argument("--" + option, type=Path, required=True)
    installer = sub.add_parser("install")
    installer.add_argument("path", type=Path)
    for name in ("launch", "terminate", "logs"):
        app = sub.add_parser(name)
        app.add_argument("bundle_id")
        if name == "logs":
            app.add_argument("--seconds", type=float, default=5)
            app.add_argument("--limit", type=int, default=200)
    ui = sub.add_parser("ui").add_subparsers(dest="operation", required=True)
    for name in ("screenshot", "observe", "tree"):
        ui.add_parser(name)
    for name in ("tap", "long-press"):
        action = ui.add_parser(name)
        action.add_argument("--x", type=float, required=True)
        action.add_argument("--y", type=float, required=True)
        if name == "long-press":
            action.add_argument("--duration", type=float, default=1)
    swipe = ui.add_parser("swipe")
    swipe.add_argument("--from", dest="start", type=lambda v: numbers(v, 2), required=True)
    swipe.add_argument("--to", dest="end", type=lambda v: numbers(v, 2), required=True)
    swipe.add_argument("--duration", type=float, default=0.6)
    ui.add_parser("type").add_argument("text")
    ui.add_parser("press").add_argument(
        "button", choices=["home", "lock", "volume-up", "volume-down", "mute"]
    )
    ui.add_parser("tap-id").add_argument("identifier")
    condition = ui.add_parser("wait-id")
    condition.add_argument("identifier")
    condition.add_argument("--seconds", type=float, default=10)
    capture = sub.add_parser("capture").add_subparsers(dest="operation", required=True)
    for name in ("periodic", "record"):
        recorder = capture.add_parser(name)
        recorder.add_argument("--seconds", type=float, default=5)
        recorder.add_argument("--interval", type=float, default=1)
    comparison = sub.add_parser("compare")
    comparison.add_argument("before", type=Path)
    comparison.add_argument("after", type=Path)
    comparison.add_argument("--roi", type=lambda v: numbers(v, 4, int))
    comparison.add_argument("--threshold", type=float, default=0.01)
    workflow = sub.add_parser("workflow").add_subparsers(dest="operation", required=True)
    interaction = workflow.add_parser("interact-verify")
    interaction.add_argument("--x", type=float, required=True)
    interaction.add_argument("--y", type=float, required=True)
    interaction.add_argument("--wait", type=float, default=0.5)
    interaction.add_argument("--roi", type=lambda v: numbers(v, 4, int))
    interaction.add_argument("--threshold", type=float, default=0.01)
    interaction.add_argument("--assert-identifier")
    run = workflow.add_parser("run")
    run.add_argument("file", type=Path)
    run.add_argument("--max-actions", type=int, default=20)
    run.add_argument("--workflow-timeout", type=float, default=120)
    run.add_argument("--stop-file", type=Path)
    sub.add_parser("mcp")
    return root


async def dispatch(args, config):
    command = args.command
    if command == "doctor":
        return doctor()
    if command == "build":
        return await build(args.project, config.artifacts, args.build_timeout, args.configuration)
    if command == "sign":
        return await sign(args.app, args.key, args.profile, args.output, config.artifacts)
    if command == "package":
        return package_ipa(args.app, args.output)
    if command == "compare":
        return compare(args.before, args.after, args.roi, args.threshold)
    api = AsyncRemoteIOS(config)
    if command == "devices" and args.operation == "list":
        return {
            "devices": await api.devices(),
            "configured_only": bool(config.devices),
            "connection_verified": False,
            "simulated": config.backend == "mock",
        }
    if command == "device" and args.operation == "disconnect":
        raise unsupported(
            "persistent_disconnect",
            "Sessions are process-scoped. Stop the owning connect --hold process; tunnels close on exit.",
        )
    session = await api.session()
    if args.orientation:
        session.device = replace(session.device, orientation=args.orientation)
    async with session:
        if command in {"devices", "device"}:
            result = await session.status()
            if command == "device" and args.operation == "connect":
                if not 0 <= args.hold <= 3600:
                    raise RemoteIOSError("invalid_argument", "hold must be 0..3600 seconds")
                if args.hold:
                    print(
                        json.dumps({"event": "connected", "result": serializable(result)}),
                        file=sys.stderr,
                        flush=True,
                    )
                    await asyncio.sleep(args.hold)
            result["connection_closed_on_command_exit"] = True
            return result
        if command == "install":
            return await session.install(args.path)
        if command in {"launch", "terminate"}:
            return await getattr(session, command)(args.bundle_id)
        if command == "logs":
            return await session.logs(args.bundle_id, args.seconds, args.limit)
        if command == "ui":
            op = args.operation
            if op in {"tree", "tap-id", "wait-id"}:
                from remote_ios_agent.automation.wda import WDA

                client = WDA(session.device.wda_url, session.device.wda_session)
                if op == "tree":
                    return {"tree": await client.tree(), "backend": "wda"}
                if op == "tap-id":
                    return await client.tap(args.identifier)
                return await client.wait(args.identifier, args.seconds)
            if op in {"screenshot", "observe"}:
                return await getattr(session, op)()
            if op == "tap":
                return await session.tap(args.x, args.y)
            if op == "long-press":
                return await session.long_press(args.x, args.y, args.duration)
            if op == "swipe":
                return await session.swipe(args.start, args.end, args.duration)
            if op == "type":
                return await session.type_text(args.text)
            if op == "press":
                return await session.press(args.button)
        if command == "capture":
            from remote_ios_agent.capture.video import periodic, record

            return await (record if args.operation == "record" else periodic)(
                session, args.seconds, args.interval
            )
        if command == "workflow":
            if args.operation == "interact-verify":
                result = await interact_verify(
                    session,
                    args.x,
                    args.y,
                    wait=args.wait,
                    roi=args.roi,
                    threshold=args.threshold,
                    assert_identifier=args.assert_identifier,
                )
                if not result["ui_changed"]:
                    raise RemoteIOSError(
                        "no_visual_change", "No UI change above threshold", details=serializable(result)
                    )
                return result
            spec = json.loads(args.file.read_text())
            steps = spec["steps"] if isinstance(spec, dict) else spec
            if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
                raise RemoteIOSError("invalid_workflow", "Expected a list of step objects")
            report = await execute(
                session,
                steps,
                max_actions=args.max_actions,
                timeout=args.workflow_timeout,
                stop_file=args.stop_file,
            )
            if report["status"] != "completed":
                raise RemoteIOSError("workflow_incomplete", report["status"], details=report)
            return report
    raise RemoteIOSError("invalid_arguments", "Unsupported command")


def main():
    from remote_ios_agent.core.logging import configure_logging

    configure_logging()
    try:
        args = parser().parse_args()
        config = Config.load(
            args.config,
            selected=args.device,
            backend=args.backend,
            artifacts=args.artifacts,
            timeout=args.timeout,
        )
        if args.command == "mcp":
            from remote_ios_agent.mcp.server import create_server

            create_server(config).run(transport="stdio")
            return
        result = asyncio.run(dispatch(args, config))
        print(json.dumps({"ok": True, "result": serializable(result)}, ensure_ascii=False))
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": {"code": "cancelled", "message": "Session cancelled"}}))
        raise SystemExit(130) from None
    except Exception as exc:
        if isinstance(exc, RemoteIOSError):
            error = exc.as_dict()
        elif isinstance(exc, (ValueError, OSError, KeyError, TypeError)):
            error = {"code": "invalid_input", "message": str(exc)}
        else:
            error = {"code": "unexpected_error", "message": type(exc).__name__}
        print(json.dumps({"ok": False, "error": serializable(error)}, ensure_ascii=False))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
