# Compatibility matrix

This table distinguishes implemented adapters from measured end-to-end support. A passing mock test is never device evidence.

| Area | Implemented / intended scope | Validation / gate |
|---|---|---|
| Python | 3.12+; optional pymobiledevice3 11.48.0 | Local Python 3.12 tests; Linux CI matrix in validation report |
| Linux hosts | Ubuntu/Debian; x86_64 and ARM64 | CI tests use mock; hardware transport still unverified |
| Desktop | None required | CLI, stdio MCP and Python work headlessly |
| USB | Existing trust; preferred upstream tunnel | No USB iPhone visible during implementation |
| Direct RSD | Explicit routable host/port, exact UDID | Adapter contract tested; no configured endpoint |
| RemotePairing/Tailscale | Explicit phone endpoint and existing record; kernel TUN | No local RemotePairing record; actual loop blocked |
| iOS 17.4+ | Upstream userspace tunnel route | Service/version-specific; not a guarantee of every HID feature |
| iOS 17.0–17.3 | Different tunnel requirements | macOS native fallback is not a Linux solution |
| iOS 26 remote bootstrap | Upstream reported restrictions | Do not assume wireless Linux pairing works |
| iOS 27 remote tailnet | Upstream 27.0.1 report exists | Not replicated here; cellular-only route may fail |
| Install/launch/terminate | Installation proxy and DVT; lookup/PID verification | Adapter tested, real deployment unverified |
| Native coordinate UI | Authenticated CoreDevice media + universal HID | No WDA required; real device verification pending |
| Native text | US-layout ASCII, tab and newline | Full-string validation; Unicode unsupported |
| Rotation | Explicit orientation transforms; dimension guard | Unit tests only; no automatic sensor discovery |
| Screenshot | CoreDevice PNG | Mock artifacts verified; native service unverified |
| Video | Periodic screenshot MP4 via FFmpeg | Native HEVC/MJPEG not implemented |
| WDA | Existing signed/running session; tree, ID tap, visible wait | HTTP contract tests; real XCTest provisioning pending |
| SwiftPM app build | Optional xtool + compatible Swift/Darwin SDK | No SDK/xtool installed locally; Linux iOS build unverified |
| Xcode project build | Requires reviewed conversion to xtool/SwiftPM | Direct `.xcodeproj` input explicitly unsupported |
| Signing | Optional external zsign; existing signed IPA accepted | No real identity/profile used |
| Grok | Generic shell/stdio MCP recipe | No Grok runtime access supplied |
| Swift SDK | Opt-in local typed registry and diagnostics | macOS Swift tests; transport/feedback/capture deferred |
| ScreenCaptureKit | Apple documentation says iOS 27+ | Researched only; not part of implemented SDK |

The environment used for local checks was macOS ARM64, not the target cloud host. See [validation](validation.md) for exact results and [upstream review](research/upstreams.md) for versions/licenses.
