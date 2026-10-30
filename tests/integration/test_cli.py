import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "remote_ios_agent.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=15,
        env={k: v for k, v in os.environ.items() if not k.startswith("REMOTE_IOS_")},
    )


def test_mock_cli_loop(tmp_path):
    result = cli(
        "--backend",
        "mock",
        "--artifacts",
        str(tmp_path),
        "workflow",
        "interact-verify",
        "--x",
        "200",
        "--y",
        "400",
        "--wait",
        "0",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] and payload["result"]["simulated"]
    assert payload["result"]["comparison"]["changed"]
    assert not payload["result"]["verified"]


def test_cli_unchanged_is_failure(tmp_path):
    result = cli(
        "--backend",
        "mock",
        "--artifacts",
        str(tmp_path),
        "workflow",
        "interact-verify",
        "--x",
        "1",
        "--y",
        "1",
        "--wait",
        "0",
    )
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "no_visual_change"
    assert payload["error"]["details"]["before"]["path"]


def test_argument_errors_are_json():
    result = cli("ui", "tap", "--x", "abc", "--y", "1")
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == "invalid_arguments"


def test_xcode_project_not_claimed_as_supported():
    result = cli("build", "Demo.xcodeproj")
    assert json.loads(result.stdout)["error"]["code"] == "capability_unavailable"


def test_mock_is_never_fallback(tmp_path):
    config = tmp_path / "bad.toml"
    config.write_text('[devices.real]\nidentifier="wrong"\ntransport="rsd"\nhost="127.0.0.1"\nport=1\n')
    result = cli("--config", str(config), "--timeout", "1", "device", "connect")
    payload = json.loads(result.stdout)
    assert not payload["ok"]
    assert "simulated" not in payload
