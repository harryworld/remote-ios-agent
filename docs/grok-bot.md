# Grok Bot setup and demo

Grok Bot is the first intended cloud environment, but no Grok-specific runtime/API is required. This guide assumes a Linux shell with Python 3.12+, package installation allowed, and network access to your tailnet. Actual Grok shell/MCP/network privileges were not available in the implementation environment and remain an acceptance-test requirement.

```sh
git clone https://github.com/harryworld/remote-ios-agent.git
cd remote-ios-agent
./scripts/install-linux.sh
source .venv/bin/activate
remote-ios doctor
./scripts/smoke.sh
```

The smoke workflow is explicitly simulated and verifies CLI/orchestration, JSON results, capture files and failure handling. It is not a phone test. In a reproducible CI setup use `uv sync --frozen --all-extras` instead of the convenience pip installer.

Prepare the phone and pairing record per [device setup](device-setup.md), join the host to the restricted tailnet, and configure `remote-ios.toml`. Do not assume a cloud container permits `/dev/net/tun`, NET_ADMIN, multicast, or inbound media. If TUN is unavailable, supply an already established, routed RSD endpoint; generic HTTP proxying will not suffice. If the environment cannot carry the required tunnel/media path, record that blocker and use another permitted host rather than reporting success.

## Agent instructions

Load [AGENT.md](../examples/agent-workflows/AGENT.md). An agent with shell execution can use the CLI directly. If Grok supports standard MCP stdio, use [the generic MCP configuration](mcp.md). This repository makes no claim that every Grok account/product supports MCP, background processes, or Tailscale.

## Physical end-to-end demo

1. Configure Swift/xtool and an authorized Darwin SDK, then run `remote-ios build examples/demo-ios-app`.
2. Sign the resulting app with a development identity/profile valid for the chosen device (see [build](build.md)).
3. Run `remote-ios device status`, install and launch the app.
4. Capture a screenshot and read the actual button's pixel coordinates. Device dimensions differ from the mock.
5. Export explicit demo inputs and run:

```sh
export REMOTE_IOS_CONFIG="$PWD/remote-ios.toml"
export REMOTE_IOS_DEVICE=phone
export REMOTE_IOS_TEST_IPA="$PWD/build/Demo.ipa"
export REMOTE_IOS_TEST_BUNDLE=com.example.RemoteIOSDemo
export REMOTE_IOS_TEST_X=ACTUAL_PIXEL_X
export REMOTE_IOS_TEST_Y=ACTUAL_PIXEL_Y
./scripts/physical-demo.sh
```

6. Inspect the before/after PNGs and confirm the displayed counter increments. If WDA is configured, assert `counter-1` rather than relying only on pixel differences.
7. Require actual app logs, machine-readable results, and a second successful iteration before marking acceptance complete. Archive toolchain versions and sanitized evidence in a new validation report.

The demo script stops on command failure. A zero exit from a HID operation is never the acceptance criterion. `tests/hardware/test_acceptance.py` is opt-in and checks installed/launched app, changed capture and nonempty logs; Linux build and Grok orchestration still require separate recorded evidence.
