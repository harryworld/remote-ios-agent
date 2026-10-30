from unittest.mock import AsyncMock

import pytest

from remote_ios_agent.automation.wda import WDA
from remote_ios_agent.core.errors import RemoteIOSError


async def test_wda_element_click_and_wait():
    client = WDA("http://127.0.0.1:8100", "session")
    client.request = AsyncMock(side_effect=[{"element-6066-11e4-a52e-4f735466cecf": "element"}, None])
    result = await client.tap("increment")
    assert result["verified"] is False
    assert client.request.call_args_list[-1].args == ("/element/element/click", {})
    client.request = AsyncMock(side_effect=[{"ELEMENT": "element"}, True])
    assert (await client.wait("counter-1"))["visible"]


async def test_wda_timeout():
    client = WDA("http://127.0.0.1:8100", "session")
    client.request = AsyncMock(side_effect=RemoteIOSError("wda_error", "no such element"))
    with pytest.raises(RemoteIOSError) as error:
        await client.wait("missing", timeout=0.01)
    assert error.value.code == "condition_timeout"
