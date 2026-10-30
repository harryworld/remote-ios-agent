# remote-ios-agent

Linux-first CLI, Python API, and MCP tools for remote **physical iPhones**. No desktop environment or agent vendor is required.

**Status: experimental 0.1 foundation. The Linux → physical iPhone acceptance milestone is not yet verified.** Real operations use pymobiledevice3, never a silent mock fallback. See [validation evidence](docs/validation.md), [compatibility](docs/compatibility.md), and [roadmap](docs/roadmap.md).

## Set up with Grok Bot

Copy and paste this entire prompt into Grok Bot. It requires no edits before use: Grok should discover existing setup and ask for the device-specific inputs it cannot obtain. You may need to complete Tailscale sign-in, iPhone trust/Developer Mode, and secure provisioning of pairing and signing files.

```text
Set up remote-ios-agent on this Linux cloud computer and work toward a verified
remote physical-iPhone development loop. Perform the setup and run the checks;
do not stop after giving me a plan or installation instructions.

Repository: https://github.com/harryworld/remote-ios-agent

1. Inspect this host's OS, architecture, Python, installed tools, permissions,
   network access and existing device/build setup. Reuse working installations
   and preserve unrelated files. Clone the repository into a suitable workspace,
   or inspect an existing checkout without resetting local changes. Read README.md,
   examples/agent-workflows/AGENT.md and docs/{installation,grok-bot,device-setup,
   build,compatibility,mcp,workflows,troubleshooting}.md before configuring it.

2. Install the missing Linux prerequisites using the host's supported package
   manager: Python 3.12+, venv support, Git, required native libraries, and FFmpeg
   for sampled video. Install uv from its official distribution if needed. In
   the repository, run:
     uv sync --frozen --all-extras
     uv run remote-ios doctor
     uv run pytest -m 'not hardware' -q
     uv run remote-ios --backend mock workflow run examples/agent-workflows/smoke.json
   Label these results as simulated; they do not prove phone access. Use
   `uv run remote-ios` for subsequent commands so the environment stays consistent.

3. Install/configure Tailscale where this environment permits it and help me
   complete sign-in. Discover available devices and existing pairing records
   without printing credentials. Ask only for missing inputs: the target iPhone's
   UDID, tailnet address and actual RemotePairing port (or a prepared RSD endpoint),
   plus secure local paths to required pairing/signing files. Never ask me to paste
   private keys or pairing-record contents into chat. Explain any necessary
   one-time USB trust, Developer Mode, developer disk image or Mac provisioning step.
   Tailscale connectivity alone does not establish Apple pairing or HID access.

4. Create the ignored remote-ios.toml from examples/remote-ios.example.toml using
   verified values, explicit device selection and the correct orientation. Check
   TUN permissions, tunnel routing and the media return path. If this cloud host
   cannot create a tunnel, investigate an already prepared, routed RSD endpoint.
   Do not expose device services publicly or treat an HTTP forward as an Apple
   tunnel. Run device status and report actual capabilities and connection errors.

5. Follow docs/build.md to install a compatible Linux Swift toolchain and xtool,
   configure an authorized Apple SDK supplied through a secure path, and prepare
   signing with a valid development identity/profile. Use the repository's setup
   helpers where applicable. Do not download unofficial SDK copies or claim that
   arbitrary Xcode projects work. Build examples/demo-ios-app on Linux, sign its
   exact output, install it on the selected iPhone, and launch its bundle ID.
   An existing signed demo IPA can unblock device testing, but does not count as
   a successful Linux build.

6. Capture the actual phone screen, locate the demo's Increment button in screenshot
   pixels, tap it through native HID, and save before/after captures and JSON results.
   Confirm the displayed counter increases, collect actual app logs, and repeat
   the interaction without manual intervention. Use an appropriate comparison ROI;
   a command exit or unrelated pixel change is not proof of successful interaction.
   Try periodic capture and sampled video separately. Keep WDA optional; configure
   its hierarchy/assertion tools only if a compatible signed runner is available.

7. If this Grok environment supports MCP stdio, configure the server using docs/mcp.md
   with this checkout's actual executable/config paths, then verify tool discovery
   and a device query. Otherwise use the CLI directly. Do not assume Grok-specific
   APIs or browser automation. The SDK WebSocket/feedback transport and native
   video are deferred features; report them as unavailable rather than fabricating
   setup or success.

Continue independent setup when a step is blocked. Use bounded timeouts/action
counts, stop on unexpected device effects, and observe before retrying an action
whose outcome is uncertain. Keep credentials and private captures out of Git.
Finish with installed versions, working commands, configuration/artifact paths,
executed checks, real versus simulated results, exact blockers, and the smallest
remaining action I need to take. Mark the full loop complete only after the Linux
build and repeated physical-device workflow have actually succeeded.
```

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

[Workflows](docs/workflows.md) · [Architecture](docs/architecture.md) · [Research/licenses](docs/research/upstreams.md) · [Installation](docs/installation.md) · [Troubleshooting](docs/troubleshooting.md).

Python toolkit: GPL-3.0-only, compatible with pymobiledevice3. Independent Swift SDK: MIT; see its own LICENSE. No upstream setup scripts or SDK binaries are vendored.
