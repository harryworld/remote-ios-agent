import plistlib
import zipfile
from pathlib import Path

from remote_ios_agent.core.errors import RemoteIOSError


def bundle_identifier(path: Path) -> str:
    try:
        if path.is_dir() and path.suffix == ".app":
            data = (path / "Info.plist").read_bytes()
        elif path.suffix == ".ipa":
            with zipfile.ZipFile(path) as archive:
                names = [
                    n
                    for n in archive.namelist()
                    if n.startswith("Payload/") and n.count("/") == 2 and n.endswith(".app/Info.plist")
                ]
                if len(names) != 1:
                    raise ValueError("IPA needs exactly one top-level app")
                data = archive.read(names[0])
        else:
            raise ValueError("Expected an .app directory or .ipa file")
        return plistlib.loads(data)["CFBundleIdentifier"]
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise RemoteIOSError("invalid_package", str(exc)) from exc


def package_ipa(app: Path, output: Path) -> dict:
    identifier = bundle_identifier(app)
    if not app.is_dir():
        raise RemoteIOSError("invalid_package", "Packaging requires an .app directory")
    output = output.resolve()
    if output.is_relative_to(app.resolve()):
        raise RemoteIOSError("invalid_package", "Output must be outside the app bundle")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_symlink():
                raise RemoteIOSError("invalid_package", "Symlinks require a platform-aware packaging tool")
            if path.is_file():
                archive.write(path, Path("Payload") / app.name / path.relative_to(app))
    return {
        "path": str(output),
        "bundle_id": identifier,
        "signature_validated": False,
        "note": "Packaging preserves existing signatures; it does not sign or validate provisioning.",
    }
