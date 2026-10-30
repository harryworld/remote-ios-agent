# Milestones

## 0.1 foundation (implemented; hardware acceptance outstanding)

- Portable CLI, Python API and optional MCP stdio server.
- Native pymobiledevice3 transport/install/launch/log/capture/HID adapters.
- Explicit selection, capability advertisements, typed results, bounded workflows and artifact evidence.
- Mock CI backend, adapter-contract tests, error/timeout tests and stdio MCP integration.
- Optional xtool/zsign adapters, IPA packaging, SwiftUI demo.
- Optional WDA client, periodic screenshots/sampled video, ROI comparison.
- Opt-in local Swift SDK registry; full transport deliberately deferred.

## Next: demonstrate the physical Linux loop

This is the priority milestone. Prepare a paired iPhone and compatible DDI, Tailscale route with media return path, Linux host (ideally Grok), and authorized Swift/SDK/signing inputs. Build the demo on Linux, install/launch, tap its button through native HID, preserve before/after PNGs, verify its counter and actual logs, repeat twice without manual intervention, then publish sanitized receipts. Check portrait and both landscape rotations, disconnect/reconnect and failure recovery. Until then the user's definition of done is **not met**.

## Subsequent increments

1. Add safe read-only connection recovery with explicit retry budgets; never replay unknown-effect actions.
2. Implement the authenticated outbound SDK WebSocket protocol and private broker, action authorization/correlation, and state/feedback endpoints.
3. Add feedback preview/redaction UI and permission-aware iOS 27 ScreenCaptureKit rolling clips; ReplayKit/app-owned screenshot fallback.
4. Validate native CoreDevice HEVC capture, optional WDA MJPEG, and browser viewer as independent backends.
5. Add visual regression baselines with masks/threshold policies and richer diagnostics.
6. Add a bounded agent-selected exploratory loop and feedback reproduction workflow only after action/stop/verification contracts are proven.

The current workflow runner supplies bounded primitives for build/inspect, interact/verify, capture/compare and externally chosen exploration steps. It does not implement autonomous source modification, issue diagnosis, or feedback ingestion. Agents can orchestrate those outside the core using the canonical CLI.
