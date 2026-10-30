import platform
import shutil
import uuid
from pathlib import Path

from remote_ios_agent.core.errors import RemoteIOSError, unsupported
from remote_ios_agent.core.process import run
from remote_ios_agent.deployment.package import bundle_identifier


def doctor() -> dict:
    executables = {name: shutil.which(name) for name in ("swift", "xtool", "clang", "ld.lld", "zsign", "ffmpeg", "tailscale")}
    return {"platform": platform.system(), "architecture": platform.machine(), "tools": executables,
            "device_dependencies_installed": __import__("importlib.util", fromlist=["find_spec"]).find_spec("pymobiledevice3") is not None,
            "note": "Executable presence is not SDK, signing, tunnel, or device-loop validation."}


async def build(project: str | Path, artifacts: Path, timeout: float = 600, configuration: str = "debug") -> dict:
    project = Path(project).resolve()
    if project.suffix in {".xcodeproj", ".xcworkspace"}:
        raise unsupported("xcode_project_build", "Convert and review a SwiftPM/xtool adapter first; xcodebuild is not available on Linux")
    if not (project / "Package.swift").is_file() or not (project / "xtool.yml").is_file():
        raise RemoteIOSError("invalid_project", "Expected Package.swift and xtool.yml in project directory")
    if configuration not in {"debug", "release"}:
        raise RemoteIOSError("invalid_argument", "configuration must be debug or release")
    job = artifacts.resolve() / f"build-{uuid.uuid4().hex}"
    await run(["xtool", "dev", "build", "--configuration", configuration], cwd=project,
              timeout=timeout, log=job / "build.log")
    apps = list((project / "xtool").glob("*.app"))
    if len(apps) != 1:
        raise RemoteIOSError("build_artifact_ambiguous", "Expected exactly one .app in project's xtool output")
    bundle = bundle_identifier(apps[0])
    return {"path": str(apps[0]), "bundle_id": bundle, "log": str(job / "build.log"),
            "host_platform": platform.system(), "signing": "not_validated", "backend": "xtool"}


async def sign(app: Path, key: Path, profile: Path, output: Path, artifacts: Path) -> dict:
    # Optional local signer: no credentials in config, logs, environment dumps or shell strings.
    for path in (app, key, profile):
        if not path.exists():
            raise RemoteIOSError("artifact_missing", str(path))
    output = output.resolve()
    if output.exists() or output.is_relative_to(app.resolve()):
        raise RemoteIOSError("invalid_argument", "Signing output must be new and outside app bundle")
    output.parent.mkdir(parents=True, exist_ok=True)
    await run(["zsign", "-k", str(key.resolve()), "-m", str(profile.resolve()), "-o", str(output), str(app.resolve())],
              timeout=120, log=artifacts / f"sign-{uuid.uuid4().hex}.log")
    identifier = bundle_identifier(output)
    return {"path": str(output), "bundle_id": identifier, "signer": "zsign",
            "device_acceptance_verified": False, "note": "Requires an unencrypted signing key; install verifies device acceptance."}
