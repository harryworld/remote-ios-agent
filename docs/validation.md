# Validation evidence — 2026-10-30

## Acceptance status

**Not complete:** the required Grok/Linux → build → remote physical iPhone → tap → verified state change loop has not been executed. The current repository is an implemented/tested foundation with real adapters and explicitly simulated integration tests.

## Executed locally

Host: macOS ARM64 (Darwin 25.6.0), Python 3.12.9, pymobiledevice3 11.48.0, Swift 6.2.4. This is not Linux or Grok.

| Check | Actual result |
|---|---|
| Python unit/integration suite | 42 passed; hardware test deselected; includes coordinates, evidence, failure preservation, cancellation cleanup, subprocess deadlines, API/CLI, WDA contracts, and real stdio MCP handshake |
| Ruff lint + format | Passed; shell scripts also passed `bash -n` |
| Packaging | Wheel and sdist built; all source Python modules present; independent Swift SDK included in sdist |
| Structured events | Parsed operation events as JSON from stderr; stdout remained valid CLI JSON |
| Mock smoke workflow | Four steps completed: simulated launch, observe, tap/change comparison, simulated log collection |
| Mock before/after capture | PNGs and sidecars saved; `simulated=true`, dispatched action remains unverified |
| Sampled video | FFmpeg produced H.264 MP4, 390×844, 1.28s (ffprobe verified) from mock screenshots; not native device streaming |
| Swift SDK Debug | Built and 1 XCTest passed; typed action, opt-in, disable, redaction and duplicate registration |
| Swift SDK Release | Built and 1 XCTest passed; enabling leaves registry disabled |
| Real `pymobiledevice3 usbmux list` | `[]` |
| Real `remote-ios devices list` | `devices: []`, `connection_verified: false`, `simulated: false` |
| Real `remote-ios device connect` | Failed with `device_selection`, `matches: 0`; no simulated fallback |
| Build attempt on demo | Failed with `dependency_missing`: `Executable not found: xtool` |
| `swift sdk list` | `No Swift SDKs are currently installed.` |
| Tailscale | Daemon running; one online iOS peer; version mismatch warning between client/server. No RemotePairing record in the usual local pymobiledevice3 directory |
| Docker | Client installed; daemon socket absent; local image execution not performed |
| Grok Bot | No supplied runtime/host access; guide and generic shell/MCP integration only |

The installed Apple device listing tool also returned simulator/same-machine records and a known physical-device record; those are not proof of a currently reachable/pymobiledevice3-paired iPhone. No real app was installed, launched, tapped, recorded or logged in this session. No signing identity or provisioning profile was used.

The first sandboxed GitHub/Tailscale probes could not access their host/network resources. Re-running the authorized read-only probes with host access confirmed GitHub authentication and a running Tailscale daemon. Those initial sandbox failures were not product defects or final authentication blockers.

## Linux CI

The repository configures Ubuntu 24.04 x86_64 and ARM64, Python 3.12/3.13, frozen dependencies, unit/integration tests, lint, and a mock smoke workflow. The [implementation CI run](https://github.com/harryworld/remote-ios-agent/actions/runs/41009973315) at `4a79f8d` passed all four Ubuntu Python jobs (42 tests each), lint/format, the mock smoke workflow, and Docker. The Swift job is recorded after completion below. The first published run failed only on build-adapter formatting; that was corrected before these passing results. CI does not provision Apple SDKs or hardware and must not be called a Linux iOS build/device acceptance test.

## Evidence handling

Generated captures/video/logs remain in ignored local `artifacts/`, with private paths/identifiers excluded from public receipts. Reproduce the simulated checks with `scripts/smoke.sh`. Real hardware testing is opt-in via `REMOTE_IOS_HARDWARE_TEST=1`, explicit config/device, signed demo IPA/bundle and screenshot pixel coordinates. Preserve the resulting report and visually confirm the expected counter value; require actual app logs, a Linux build receipt and a second unattended iteration before changing acceptance status.
