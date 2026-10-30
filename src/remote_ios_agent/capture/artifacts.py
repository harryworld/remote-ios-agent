import json
import os
import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from remote_ios_agent.core.errors import RemoteIOSError
from remote_ios_agent.core.models import Capture, serializable, timestamp


def private_directory(path: Path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)


def write_json(path: Path, data) -> None:
    private_directory(path.parent)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(serializable(data), stream, indent=2)
    temporary.replace(path)


def save_capture(
    data: bytes,
    directory: Path,
    *,
    device,
    session_id,
    action_id=None,
    application_identifier=None,
    orientation="portrait",
    simulated=False,
) -> Capture:
    with Image.open(BytesIO(data)) as image:
        image.load()
        width, height = image.size
        # Normalize encoded format into PNG rather than assuming every service emits PNG.
        directory = directory.resolve()
        private_directory(directory)
        path = directory / f"{uuid.uuid4().hex}.png"
        with path.open("xb") as stream:
            os.chmod(path, 0o600)
            image.save(stream, format="PNG")
    capture = Capture(
        path,
        device,
        timestamp(),
        width,
        height,
        orientation,
        "mock" if simulated else "coredevice_screencapture",
        session_id,
        action_id,
        application_identifier,
        simulated=simulated,
    )
    write_json(path.with_suffix(".json"), capture)
    return capture


def compare(
    before: Path, after: Path, roi: tuple[int, int, int, int] | None = None, threshold: float = 0.01
) -> dict:
    if not 0 <= threshold <= 1:
        raise RemoteIOSError("invalid_argument", "threshold must be 0..1")
    with Image.open(before) as left, Image.open(after) as right:
        if left.size != right.size:
            raise RemoteIOSError(
                "geometry_changed", "Screenshot size changed; re-observe orientation before retrying"
            )
        a, b = left.convert("RGB"), right.convert("RGB")
        if roi:
            x, y, w, h = roi
            if not (0 <= x < x + w <= a.width and 0 <= y < y + h <= a.height):
                raise RemoteIOSError("invalid_argument", "ROI must be x,y,width,height within screenshot")
            box = (x, y, x + w, y + h)
            a, b = a.crop(box), b.crop(box)
        diff = ImageChops.difference(a, b)
        difference = sum(ImageStat.Stat(diff).mean) / (3 * 255)
        return {
            "changed": difference > threshold,
            "normalized_mean_difference": difference,
            "threshold": threshold,
            "roi": roi,
            "evidence": "visual_change_only",
            "causal_verification": False,
            "limitation": "Animations, clocks and unrelated updates may change pixels; prefer ROI plus an app assertion.",
        }
