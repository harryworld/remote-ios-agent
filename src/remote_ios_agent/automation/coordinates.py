import math

from remote_ios_agent.core.errors import RemoteIOSError


def normalize(x: float, y: float, width: int, height: int, orientation: str = "portrait") -> tuple[int, int]:
    """Screenshot pixel axes -> native portrait digitizer axes. Explicit orientation is required.

    UIKit landscape-left means home indicator at the right; rotate screenshot coordinates
    back to the native portrait surface. Width/height are from the current screenshot.
    """
    if not all(math.isfinite(v) for v in (x, y)) or not (0 <= x < width and 0 <= y < height):
        raise RemoteIOSError("invalid_coordinates", f"Point outside {width}x{height} screenshot")
    u, v = x / width, y / height
    if orientation == "landscape-left":
        u, v = v, 1 - u
    elif orientation == "landscape-right":
        u, v = 1 - v, u
    elif orientation == "portrait-upside-down":
        u, v = 1 - u, 1 - v
    elif orientation != "portrait":
        raise RemoteIOSError("orientation_unknown", "Provide the device's current orientation")
    return round(u * 65535), round(v * 65535)
