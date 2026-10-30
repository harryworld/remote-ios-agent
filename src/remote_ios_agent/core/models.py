from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def serializable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return serializable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    return value


@dataclass(frozen=True)
class DeviceInfo:
    identifier: str
    name: str
    transport: str
    os_version: str | None = None
    simulated: bool = False


@dataclass(frozen=True)
class Capability:
    available: bool
    reason: str
    evidence: str = "not_probed"


@dataclass(frozen=True)
class Capture:
    path: Path
    device_identifier: str
    timestamp: str
    width: int
    height: int
    orientation: str
    method: str
    session_id: str
    action_id: str | None = None
    application_identifier: str | None = None
    application_source: str = "caller_context_not_foreground_detection"
    simulated: bool = False


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    session_id: str
    operation: str
    status: str = "dispatched"
    verified: bool = False
    simulated: bool = False
