import plistlib
from pathlib import Path

import pytest

from remote_ios_agent.build.runner import build
from remote_ios_agent.core.errors import RemoteIOSError


async def test_xtool_command_and_artifact(monkeypatch, tmp_path):
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "Package.swift").write_text("fixture")
    (project / "xtool.yml").write_text("fixture")
    calls = []

    async def fake_run(argv, *, cwd, timeout, log):
        calls.append((argv, cwd))
        app = cwd / "xtool" / "Demo.app"
        app.mkdir(parents=True)
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "demo"}))

    monkeypatch.setattr("remote_ios_agent.build.runner.run", fake_run)
    result = await build(project, tmp_path / "artifacts")
    assert calls == [(["xtool", "dev", "build", "--configuration", "debug"], project)]
    assert result["signing"] == "not_validated" and Path(result["path"]).exists()


async def test_build_requires_real_artifact(monkeypatch, tmp_path):
    (tmp_path / "Package.swift").touch()
    (tmp_path / "xtool.yml").touch()

    async def fake_run(*args, **kwargs):
        return {"exit_code": 0}

    monkeypatch.setattr("remote_ios_agent.build.runner.run", fake_run)
    with pytest.raises(RemoteIOSError) as error:
        await build(tmp_path, tmp_path / "artifacts")
    assert error.value.code == "build_artifact_ambiguous"
