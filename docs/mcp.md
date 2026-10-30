# MCP

Install the optional `[mcp]` extra (pinned official Python MCP SDK 2.3.0). MCP protocol handling is delegated to that SDK; a hand-written JSON-RPC server would add unnecessary compatibility risk. The transport is **stdio**, with no publicly listening network server.

Generic client configuration; adapt the schema to the actual host application:

```json
{
  "mcpServers": {
    "remote-ios": {
      "command": "/absolute/path/to/.venv/bin/remote-ios",
      "args": ["--config", "/absolute/path/to/remote-ios.toml", "mcp"]
    }
  }
}
```

Grok, Codex, Claude Code, Cursor or custom agents can use this interface where their host supports MCP. Otherwise use shell CLI commands. No specific vendor API or subscription is assumed.

Implemented tools: `ios_devices_list`, `ios_device_connect`, `ios_build`, `ios_install`, `ios_launch`, `ios_screenshot`, `ios_tap`, `ios_swipe`, `ios_type_text`, `ios_get_ui_tree` (WDA), `ios_record_video` (sampled), `ios_get_logs`, `ios_interact_verify`, `ios_run_workflow`.

Reserved tools `ios_app_get_state`, `ios_app_perform_action`, `ios_feedback_list`, `ios_feedback_get` return `capability_unavailable` with the missing milestone, rather than fake data. Backend status reports advertised service availability separately from operation or UI verification.

`ios_device_connect` is a probe whose connection closes on return. Individual tool calls create scoped sessions; `ios_run_workflow` retains a connection through its steps. Calls are serialized per server process because the upstream userspace tunnel is process-global. Use separate processes for concurrent devices and explicit selectors.

Results contain `ok` and `result` or `error`; inspect workflow status, action verification, and simulation flags. The MCP protocol itself may additionally report argument/schema errors. stdout is reserved for MCP messages; ordinary CLI JSON is not printed while serving. MCP integration tests perform a real stdio initialize/list-tools/call-tool exchange with the mock backend.

Only connect trusted local agents: build invokes a trusted local project's build tooling, and install/input operations affect real devices. This server does not provide an arbitrary shell-execution tool or embed credentials in tool schemas.
