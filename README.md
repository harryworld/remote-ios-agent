# remote-ios-agent

Linux-first CLI, Python API, and MCP tools for remote **physical iPhones**. No desktop environment or agent vendor is required.

**Status: experimental 0.1 foundation. The Linux → physical iPhone acceptance milestone is not yet verified.** Real operations use pymobiledevice3, never a silent mock fallback. See [validation evidence](docs/validation.md), [compatibility](docs/compatibility.md), and [roadmap](docs/roadmap.md).

## Install and try

Python 3.12+ on Ubuntu/Debian (x86_64 or ARM64):

```sh
git clone https://github.com/harryworld/remote-ios-agent.git
cd remote-ios-agent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[device,mcp,dev]'
remote-ios doctor
remote-ios devices list
```

For locked dependencies, install `uv` and run `uv sync --frozen --all-extras`.

Explicit simulation (no iPhone needed):

```sh
remote-ios --backend mock workflow interact-verify --x 200 --y 400 --roi 80,300,230,150
remote-ios --backend mock workflow run examples/agent-workflows/smoke.json
```

Mock artifacts are watermarked and all mock results carry `simulated: true`. A changed screenshot is not proof that a particular app action succeeded.

## Physical device loop

Pair and enable Developer Mode first; see [device setup](docs/device-setup.md). Configure an explicit device, transport, and orientation in `remote-ios.toml` using [the example](examples/remote-ios.example.toml). Tailscale supplies routing, not Apple pairing or developer services.

```sh
remote-ios --device phone device status
remote-ios build examples/demo-ios-app
# Build output is not automatically signed. See docs/build.md.
remote-ios sign examples/demo-ios-app/xtool/RemoteIOSDemo.app \
  --key /secure/developer-key.pem --profile /secure/demo.mobileprovision --output build/Demo.ipa
remote-ios --device phone install build/Demo.ipa
remote-ios --device phone launch com.example.RemoteIOSDemo
remote-ios --device phone ui screenshot
# Pick actual screenshot pixel coordinates; do not reuse mock coordinates blindly.
remote-ios --device phone workflow interact-verify --x 200 --y 400
remote-ios --device phone logs com.example.RemoteIOSDemo --seconds 5
```

Every command emits a JSON success/error envelope; failures exit nonzero. Saved PNGs include JSON sidecars with device, time, dimensions, configured orientation, method, and session/action IDs. Interaction returns `dispatched`, never an unearned `verified` claim. Workflows retain completed steps and failure evidence.

## Interfaces

```python
from remote_ios_agent import RemoteIOS

with RemoteIOS() as ios:
    device = ios.devices.first()  # errors when selection is ambiguous
    device.launch("com.example.RemoteIOSDemo")
    device.ui.tap(x=200, y=400)
    print(device.ui.screenshot().path)
```

Use `AsyncRemoteIOS` for async applications. [Python examples](examples/python/) · [MCP setup](docs/mcp.md) · [Grok Bot guide](docs/grok-bot.md).

## Scope and limits

- Native coordinate HID does **not** require WDA. It does require compatible RSD services and an authenticated media stream with a working return route.
- Optional WDA client supports hierarchy, accessibility-ID taps, and visibility waits against an existing signed/running WDA session.
- `xtool` is an optional external build tool. SwiftPM/xtool projects are the supported input; arbitrary `.xcodeproj`/`.xcworkspace` builds are explicitly rejected.
- Apple SDKs, signing keys, provisioning profiles, and pairing records are not distributed. SDK availability and applicable Apple agreements constrain cross compilation.
- Screen capture works independently of native video support. The implemented recorder creates a **sampled screenshot video**, not a realtime native stream.
- The optional Swift package currently provides an opt-in typed action/state registry only. WebSocket transport, feedback ingestion, and SDK capture are future milestones; corresponding MCP tools return `capability_unavailable`.

## Develop

```sh
uv sync --frozen --all-extras
uv run pytest -m 'not hardware'
uv run ruff check .
uv run ruff format --check .
```

[Architecture](docs/architecture.md) · [Research/licenses](docs/research/upstreams.md) · [Installation](docs/installation.md) · [Troubleshooting](docs/troubleshooting.md).

Python toolkit: GPL-3.0-only, compatible with pymobiledevice3. Independent Swift SDK: MIT; see its own LICENSE. No upstream setup scripts or SDK binaries are vendored.
