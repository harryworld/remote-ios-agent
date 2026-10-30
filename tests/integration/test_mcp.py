import json
import os
import sys

import pytest

from remote_ios_agent import Config
from remote_ios_agent.mcp.server import create_server

pytest.importorskip("mcp")
pytestmark = pytest.mark.integration


def payload(result):
    return json.loads(result.content[0].text)


async def test_tool_schema_and_capabilities(tmp_path):
    server = create_server(Config(backend="mock", artifacts=tmp_path))
    names = {tool.name for tool in await server.list_tools()}
    assert {"ios_tap", "ios_record_video", "ios_app_get_state", "ios_run_workflow"} <= names
    result = payload(await server.call_tool("ios_app_get_state", {}))
    assert result["error"]["code"] == "capability_unavailable"
    result = payload(await server.call_tool("ios_get_ui_tree", {}))
    assert not result["ok"]
    result = payload(await server.call_tool("ios_interact_verify", {"x": 200, "y": 400}))
    assert result["result"]["ui_changed"] and result["result"]["simulated"]


async def test_stdio_handshake_and_call(tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    environment = {k: v for k, v in os.environ.items() if not k.startswith("REMOTE_IOS_")}
    environment.update(REMOTE_IOS_BACKEND="mock", REMOTE_IOS_ARTIFACTS=str(tmp_path))
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "remote_ios_agent.mcp.server"], env=environment
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            assert any(t.name == "ios_screenshot" for t in tools.tools)
            result = payload(await client.call_tool("ios_device_connect", {}))
            assert result["ok"] and result["result"]["simulated"]


async def test_mcp_does_not_hide_workflow_or_observation_failure(tmp_path):
    server = create_server(Config(backend="mock", artifacts=tmp_path))
    result = payload(await server.call_tool("ios_interact_verify", {"x": 1, "y": 1}))
    assert not result["ok"] and result["error"]["code"] == "no_visual_change"
    result = payload(await server.call_tool("ios_run_workflow", {"steps": [{"operation": "unknown"}]}))
    assert not result["ok"] and result["error"]["code"] == "workflow_incomplete"
