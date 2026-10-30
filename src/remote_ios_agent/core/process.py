import asyncio
import os
import signal
from pathlib import Path

from remote_ios_agent.core.errors import RemoteIOSError


async def run(
    argv: list[str], *, cwd: Path | None = None, timeout: float = 120, log: Path | None = None
) -> dict:
    """No shell interpolation; bounded execution; kill the process group on cancellation."""
    stream = None
    try:
        if log:
            log.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            stream = log.open("wb")
            os.chmod(log, 0o600)
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            start_new_session=True,
            stdout=stream or asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        if stream:
            stream.close()
        raise RemoteIOSError("dependency_missing", f"Executable not found: {argv[0]}") from exc
    try:
        try:
            async with asyncio.timeout(timeout):
                code = await process.wait()
        except BaseException:
            if process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.wait()
            raise
        if code:
            raise RemoteIOSError(
                "process_failed",
                f"{Path(argv[0]).name} exited {code}",
                details={"exit_code": code, "log": str(log) if log else None},
            )
        return {"exit_code": code, "log": str(log) if log else None}
    except TimeoutError as exc:
        raise RemoteIOSError(
            "timeout",
            "External process exceeded deadline; process group terminated",
            details={"log": str(log) if log else None},
        ) from exc
    finally:
        if stream:
            stream.close()
