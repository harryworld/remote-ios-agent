from typing import Any


class RemoteIOSError(Exception):
    def __init__(self, code: str, message: str, *, details: Any = None, retryable: bool = False):
        super().__init__(message)
        self.code, self.details, self.retryable = code, details, retryable

    def as_dict(self) -> dict:
        return {"code": self.code, "message": str(self), "details": self.details, "retryable": self.retryable}


def unsupported(feature: str, reason: str) -> RemoteIOSError:
    return RemoteIOSError("capability_unavailable", f"{feature}: {reason}", details={"capability": feature})
