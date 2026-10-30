import asyncio
import shutil
import time
import uuid

from remote_ios_agent.capture.artifacts import private_directory, write_json
from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.process import run


async def periodic(session, seconds: float = 5, interval: float = 1):
    if not 0 < seconds <= 60 or not 0.2 <= interval <= 60 or seconds / interval > 120:
        raise RemoteIOSError(
            "invalid_argument", "Capture limited to 60 seconds and 120 frames; interval >= .2s"
        )
    start = time.monotonic()
    frames = []
    while time.monotonic() - start < seconds:
        frames.append(await session.screenshot())
        remaining = seconds - (time.monotonic() - start)
        if remaining > 0:
            await asyncio.sleep(min(interval, remaining))
    return {
        "frames": frames,
        "elapsed_seconds": time.monotonic() - start,
        "method": "periodic_screenshots",
        "simulated": session.backend.simulated,
    }


async def record(session, seconds=5, interval=1):
    if not shutil.which("ffmpeg"):
        raise unsupported("sampled_video", "Install FFmpeg, or use capture periodic for PNG artifacts")
    result = await periodic(session, seconds, interval)
    frames = result["frames"]
    if len(frames) < 2:
        raise RemoteIOSError("insufficient_frames", "Recording needs at least two captured frames")
    if len({(f.width, f.height) for f in frames}) != 1:
        raise RemoteIOSError("geometry_changed", "Orientation changed during recording; PNG frames retained")
    directory = session.config.artifacts.resolve() / session.id / f"recording-{uuid.uuid4().hex}"
    private_directory(directory)
    from datetime import datetime

    entries = []
    for i, frame in enumerate(frames):
        # Copy to safe relative names; avoid arbitrary file-path injection in ffconcat.
        name = f"frame-{i:04}.png"
        shutil.copyfile(frame.path, directory / name)
        duration = (
            (
                datetime.fromisoformat(frames[i + 1].timestamp) - datetime.fromisoformat(frame.timestamp)
            ).total_seconds()
            if i + 1 < len(frames)
            else interval
        )
        entries.extend([f"file '{name}'", f"duration {max(0.001, duration):.6f}"])
    entries.append(f"file 'frame-{len(frames) - 1:04}.png'")
    (directory / "frames.txt").write_text("\n".join(entries) + "\n")
    await run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            "frames.txt",
            "-vf",
            "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "recording.mp4",
        ],
        cwd=directory,
        timeout=120,
        log=directory / "ffmpeg.log",
    )
    metadata = {
        "path": str(directory / "recording.mp4"),
        "method": "sampled_screenshots_ffmpeg",
        "native_stream": False,
        "audio": False,
        "frames": frames,
        "session_id": session.id,
        "device_identifier": session.device.identifier,
        "simulated": session.backend.simulated,
    }
    write_json(directory / "recording.json", metadata)
    return metadata
