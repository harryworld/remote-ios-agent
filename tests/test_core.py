import asyncio
import json
import plistlib
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from remote_ios_agent import AsyncRemoteIOS, Config, RemoteIOS, RemoteIOSError
from remote_ios_agent.automation.coordinates import normalize
from remote_ios_agent.capture.artifacts import compare
from remote_ios_agent.core.config import DeviceConfig
from remote_ios_agent.deployment.package import bundle_identifier, package_ipa
from remote_ios_agent.workflows.runner import execute, interact_verify


@pytest.fixture
def config(tmp_path):
    return Config(backend="mock", artifacts=tmp_path / "artifacts", timeout=5)


@pytest.mark.parametrize(
    "point,expected", [((0, 0), (0, 0)), ((195, 422), (32768, 32768)), ((389, 843), (65367, 65457))]
)
def test_pixel_normalization(point, expected):
    assert normalize(*point, 390, 844) == expected


@pytest.mark.parametrize("x,y", [(-1, 0), (390, 0), (0, 844), (float("nan"), 1), (float("inf"), 1)])
def test_invalid_coordinates(x, y):
    with pytest.raises(RemoteIOSError, match="outside"):
        normalize(x, y, 390, 844)


def test_orientation_mapping():
    assert normalize(0, 0, 844, 390, "landscape-left") == (0, 65535)
    assert normalize(0, 0, 844, 390, "landscape-right") == (65535, 0)
    assert normalize(0, 0, 390, 844, "portrait-upside-down") == (65535, 65535)


def test_config_and_environment(tmp_path, monkeypatch):
    path = tmp_path / "config.toml"
    path.write_text(
        '[remote_ios]\ntimeout=9\n[devices.phone]\nidentifier="udid"\ntransport="rsd"\nhost="::1"\nport=1234\n'
    )
    monkeypatch.setenv("REMOTE_IOS_DEVICE", "phone")
    config = Config.load(path)
    assert config.timeout == 9
    assert config.choose(list(config.devices)).identifier == "udid"
    with pytest.raises(RemoteIOSError):
        Config.load(tmp_path / "missing")


def test_no_ambiguous_selection():
    devices = [DeviceConfig("one", "1"), DeviceConfig("two", "2")]
    with pytest.raises(RemoteIOSError, match="exactly one"):
        Config().choose(devices)
    assert Config(selected="two").choose(devices).identifier == "2"
    with pytest.raises(ValueError):
        Config(devices=(DeviceConfig("fake", "fake", "mock"),))


async def test_interaction_evidence(config):
    session = await AsyncRemoteIOS(config).session()
    async with session:
        result = await interact_verify(session, 200, 400, wait=0, roi=(80, 300, 230, 150))
        assert result["ui_changed"]
        assert not result["verified"]
        assert not result["action"].verified
        assert result["simulated"]
        sidecar = json.loads(result["after"].path.with_suffix(".json").read_text())
        assert sidecar["action_id"] == result["action"].action_id
        assert sidecar["simulated"] is True
        assert stat.S_IMODE(result["after"].path.stat().st_mode) == 0o600
    assert not session.backend.connected


async def test_no_false_positive(config):
    async with await AsyncRemoteIOS(config).session() as session:
        result = await interact_verify(session, 10, 10, wait=0)
        assert result["ui_changed"] is False
        with pytest.raises(RemoteIOSError):
            compare(result["before"].path, result["after"].path, (-1, 0, 10, 10))


async def test_workflow_failure_retains_completed_evidence(config):
    async with await AsyncRemoteIOS(config).session() as session:
        report = await execute(
            session,
            [
                {"operation": "screenshot"},
                {"operation": "tap", "arguments": {"x": -1, "y": 1}},
                {"operation": "screenshot"},
            ],
        )
        assert report["status"] == "failed"
        assert len(report["steps"]) == 2
        assert report["steps"][0]["status"] == "completed"
        saved = json.loads(Path(report["artifact"]).read_text())
        assert saved["steps"][1]["error"]["code"] == "invalid_coordinates"


async def test_limits_and_stop(config, tmp_path):
    async with await AsyncRemoteIOS(config).session() as session:
        with pytest.raises(RemoteIOSError):
            await execute(session, [{"operation": "screenshot"}] * 3, max_actions=2)
        stop = tmp_path / "stop"
        stop.touch()
        report = await execute(session, [{"operation": "screenshot"}], stop_file=stop)
        assert report["status"] == "stopped" and report["steps"] == []
        report = await execute(session, [{"operation": "wait", "arguments": {"seconds": 1}}], timeout=0.01)
        assert report["status"] == "timeout"


async def test_timeout_and_teardown(config):
    session = await AsyncRemoteIOS(replace(config, timeout=0.01)).session()
    async with session:

        async def stall():
            await asyncio.sleep(10)

        with pytest.raises(RemoteIOSError) as error:
            await session.call(stall)
        assert error.value.code == "timeout" and not error.value.retryable
    assert not session.backend.connected


async def test_orientation_mismatch_prevents_tap(config):
    config = replace(config, devices=(DeviceConfig("mock", "mock", "mock", orientation="landscape-left"),))
    async with await AsyncRemoteIOS(config).session() as session:
        with pytest.raises(RemoteIOSError) as error:
            await session.tap(100, 100)
        assert error.value.code == "orientation_mismatch"
        assert session.backend.count == 0


def test_sync_api(config):
    with RemoteIOS(config) as ios:
        device = ios.devices.first()
        device.launch("com.example.demo")
        device.ui.tap(x=200, y=400)
        assert device.ui.screenshot().path.exists()


def test_packaging(tmp_path):
    app = tmp_path / "Demo.app"
    app.mkdir()
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.example.demo"}))
    binary = app / "Demo"
    binary.write_bytes(b"fixture-not-an-executable")
    binary.chmod(0o755)
    output = tmp_path / "Demo.ipa"
    result = package_ipa(app, output)
    assert not result["signature_validated"]
    assert bundle_identifier(output) == "com.example.demo"
    with pytest.raises(RemoteIOSError):
        package_ipa(app, app / "nested.ipa")


async def test_logs_are_bounded(config):
    async with await AsyncRemoteIOS(config).session() as session:
        result = await session.logs("demo", seconds=0.01)
        assert result["count"] == 1 and result["simulated"]
