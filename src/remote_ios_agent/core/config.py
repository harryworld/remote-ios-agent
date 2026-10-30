import os
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path

from .errors import RemoteIOSError


@dataclass(frozen=True)
class DeviceConfig:
    name: str
    identifier: str
    transport: str = "usb"
    host: str | None = None
    port: int | None = None
    protocol: str = "quic"
    orientation: str = "portrait"
    wda_url: str | None = None
    wda_session: str | None = None

    def __post_init__(self):
        if self.transport not in {"usb", "rsd", "remote-pairing", "mock"}:
            raise ValueError("transport must be usb, rsd, remote-pairing, or mock")
        if self.transport in {"rsd", "remote-pairing"} and not (self.host and self.port):
            raise ValueError("network transports require explicit host and port")
        if self.port is not None and not 1 <= self.port <= 65535:
            raise ValueError("port must be 1..65535")
        if self.protocol not in {"quic", "tcp"}:
            raise ValueError("protocol must be quic or tcp")
        if self.orientation not in {"portrait", "portrait-upside-down", "landscape-left", "landscape-right"}:
            raise ValueError("invalid orientation")


@dataclass(frozen=True)
class Config:
    devices: tuple[DeviceConfig, ...] = field(default_factory=tuple)
    selected: str | None = None
    backend: str = "pmd3"
    artifacts: Path = Path("artifacts")
    timeout: float = 30

    def __post_init__(self):
        if self.backend not in {"pmd3", "mock"}:
            raise ValueError("backend must be pmd3 or mock")
        if not 0 < self.timeout <= 3600:
            raise ValueError("timeout must be >0 and <=3600 seconds")
        names = [d.name for d in self.devices]
        if len(names) != len(set(names)):
            raise ValueError("device names must be unique")
        if self.backend != "mock" and any(d.transport == "mock" for d in self.devices):
            raise ValueError("mock transport requires explicit backend=mock")

    @classmethod
    def load(cls, path: str | Path | None = None, **overrides) -> "Config":
        explicit = path or os.getenv("REMOTE_IOS_CONFIG")
        source = Path(explicit or "remote-ios.toml")
        try:
            data = tomllib.loads(source.read_text()) if source.exists() else {}
            if explicit and not source.exists():
                raise ValueError(f"config file does not exist: {source}")
            values = data.get("remote_ios", {})
            env = {
                "backend": os.getenv("REMOTE_IOS_BACKEND"),
                "selected": os.getenv("REMOTE_IOS_DEVICE"),
                "artifacts": os.getenv("REMOTE_IOS_ARTIFACTS"),
                "timeout": os.getenv("REMOTE_IOS_TIMEOUT"),
            }
            values.update({k: v for k, v in env.items() if v is not None})
            values.update({k: v for k, v in overrides.items() if v is not None})
            values["artifacts"] = Path(values.get("artifacts", "artifacts")).expanduser()
            values["timeout"] = float(values.get("timeout", 30))
            return cls(
                devices=tuple(DeviceConfig(name=n, **v) for n, v in data.get("devices", {}).items()), **values
            )
        except (ValueError, TypeError, OSError) as exc:
            raise RemoteIOSError("configuration_error", str(exc)) from exc

    def choose(self, candidates: list[DeviceConfig], selector: str | None = None) -> DeviceConfig:
        selector = selector or self.selected
        matches = [d for d in candidates if selector in (d.name, d.identifier)] if selector else candidates
        if len(matches) != 1:
            raise RemoteIOSError(
                "device_selection",
                "Select exactly one device with --device; discovery never guesses.",
                details={"matches": len(matches), "configured_names": [d.name for d in candidates]},
            )
        return matches[0]

    def selecting(self, name: str) -> "Config":
        return replace(self, selected=name)
