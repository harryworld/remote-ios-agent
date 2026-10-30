"""Opt in only on a prepared disposable demo app. Never runs in ordinary CI."""

import os

import pytest

from remote_ios_agent import AsyncRemoteIOS, Config
from remote_ios_agent.workflows.runner import interact_verify

pytestmark = pytest.mark.hardware


async def test_physical_demo_loop():
    if os.getenv("REMOTE_IOS_HARDWARE_TEST") != "1":
        pytest.skip("Set REMOTE_IOS_HARDWARE_TEST=1 and explicit config/device/demo coordinates")
    config = Config.load(os.environ["REMOTE_IOS_CONFIG"])
    assert config.backend != "mock"
    assert config.selected
    async with await AsyncRemoteIOS(config).session() as session:
        assert not session.backend.simulated
        await session.install(os.environ["REMOTE_IOS_TEST_IPA"])
        await session.launch(os.environ["REMOTE_IOS_TEST_BUNDLE"])
        result = await interact_verify(
            session,
            float(os.environ["REMOTE_IOS_TEST_X"]),
            float(os.environ["REMOTE_IOS_TEST_Y"]),
            assert_identifier=os.getenv("REMOTE_IOS_TEST_ASSERT_ID"),
        )
        assert result["ui_changed"]
        assert not result["simulated"]
        logs = await session.logs(os.environ["REMOTE_IOS_TEST_BUNDLE"], seconds=5)
        assert logs["lines"], "Need actual app log evidence for hardware acceptance"
