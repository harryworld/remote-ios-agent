import asyncio
import time
import uuid
from pathlib import Path

from remote_ios_agent.capture.artifacts import compare, write_json
from remote_ios_agent.core.errors import RemoteIOSError
from remote_ios_agent.core.models import serializable, timestamp


async def interact_verify(session, x, y, *, wait=0.5, roi=None, threshold=0.01, assert_identifier=None):
    if not 0 <= wait <= 30:
        raise RemoteIOSError("invalid_argument", "wait must be 0..30 seconds")
    # Keep authentication stream alive over the entire gesture/evidence sequence.
    async with session.interaction():
        before = await session.screenshot()
        action = await session.tap(x, y)
        await asyncio.sleep(wait)
        after = await session.screenshot(action_id=action.action_id)
    difference = compare(before.path, after.path, roi, threshold)
    assertion = None
    if assert_identifier:
        from remote_ios_agent.automation.wda import WDA

        assertion = await WDA(session.device.wda_url, session.device.wda_session).wait(assert_identifier)
    return {
        "before": before,
        "action": action,
        "after": after,
        "comparison": difference,
        "ui_changed": difference["changed"],
        "assertion": assertion,
        "verified": bool(assertion),
        "simulated": session.backend.simulated,
    }


def resolve_arguments(value, completed: list[dict]):
    """Resolve explicit prior-step result references, without expression evaluation."""
    if isinstance(value, dict):
        if "from_step" in value:
            if set(value) != {"from_step", "field"}:
                raise RemoteIOSError("invalid_reference", "Reference must have from_step and field only")
            index, field = value["from_step"], value["field"]
            if type(index) is not int or not 0 <= index < len(completed):
                raise RemoteIOSError("invalid_reference", "Reference must address a prior completed step")
            step = completed[index]
            if step["status"] != "completed" or not isinstance(field, str):
                raise RemoteIOSError("invalid_reference", "Referenced step is not completed")
            result = step["result"]
            for component in field.split("."):
                if not isinstance(result, dict) or component not in result:
                    raise RemoteIOSError("invalid_reference", "Referenced result field does not exist")
                result = result[component]
            return result
        return {key: resolve_arguments(item, completed) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_arguments(item, completed) for item in value]
    return value


async def execute(session, steps: list[dict], *, max_actions=20, timeout=120, stop_file: Path | None = None):
    if not 1 <= max_actions <= 100 or len(steps) > max_actions or not 0 < timeout <= 1800:
        raise RemoteIOSError("workflow_limit", "Workflow must fit 1..100 actions and <=1800 seconds")
    report = {
        "workflow_id": uuid.uuid4().hex,
        "session_id": session.id,
        "started_at": timestamp(),
        "steps": [],
        "status": "running",
        "simulated": session.backend.simulated,
    }
    destination = session.config.artifacts / session.id / f"workflow-{report['workflow_id']}.json"
    report["artifact"] = str(destination.resolve())
    try:
        async with asyncio.timeout(timeout):
            for index, step in enumerate(steps):
                if stop_file and stop_file.exists():
                    report["status"] = "stopped"
                    break
                operation = step.get("operation")
                args = step.get("arguments", {})
                started = time.monotonic()
                entry = {"index": index, "operation": operation, "status": "running"}
                report["steps"].append(entry)
                write_json(destination, report)
                try:
                    args = resolve_arguments(args, report["steps"][:-1])
                    if operation == "interact_verify":
                        result = await interact_verify(session, **args)
                        if not result["ui_changed"]:
                            entry["result"] = serializable(result)
                            raise RemoteIOSError(
                                "no_visual_change", "No change above threshold; action effect unverified"
                            )
                    elif operation == "build":
                        from remote_ios_agent.build.runner import build

                        result = await build(artifacts=session.config.artifacts, **args)
                    elif operation == "sign":
                        from remote_ios_agent.build.runner import sign

                        result = await sign(
                            artifacts=session.config.artifacts,
                            **{key: Path(value) for key, value in args.items()},
                        )
                    elif operation == "package":
                        from remote_ios_agent.deployment.package import package_ipa

                        result = package_ipa(Path(args["app"]), Path(args["output"]))
                    elif operation in {
                        "observe",
                        "screenshot",
                        "tap",
                        "swipe",
                        "long_press",
                        "type_text",
                        "press",
                        "install",
                        "launch",
                        "terminate",
                        "logs",
                    }:
                        result = await getattr(session, operation)(**args)
                    elif operation == "wait":
                        seconds = float(args["seconds"])
                        if not 0 <= seconds <= 30:
                            raise RemoteIOSError("invalid_argument", "Wait must be 0..30 seconds")
                        await asyncio.sleep(seconds)
                        result = {"waited": seconds}
                    elif operation in {"compare", "assert_equal"}:
                        result = compare(
                            Path(args["before"]),
                            Path(args["after"]),
                            args.get("roi"),
                            args.get("threshold", 0.01),
                        )
                        if operation == "assert_equal" and result["changed"]:
                            entry["result"] = result
                            raise RemoteIOSError(
                                "visual_regression", "Image difference exceeds threshold", details=result
                            )
                    else:
                        raise RemoteIOSError(
                            "unknown_operation", f"Unsupported workflow operation: {operation}"
                        )
                    entry.update(
                        status="completed", result=serializable(result), elapsed=time.monotonic() - started
                    )
                except Exception as exc:
                    entry.update(
                        status="failed",
                        error=exc.as_dict()
                        if isinstance(exc, RemoteIOSError)
                        else {"code": type(exc).__name__, "message": "Workflow step failed"},
                    )
                    report["status"] = "failed"
                    break
                write_json(destination, report)
            else:
                report["status"] = "completed"
    except TimeoutError:
        report["status"] = "timeout"
        if report["steps"] and report["steps"][-1]["status"] == "running":
            report["steps"][-1]["status"] = "timeout"
    finally:
        report["finished_at"] = timestamp()
        write_json(destination, report)
    return report
