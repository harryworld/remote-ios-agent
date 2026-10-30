# Upstream review — 2026-10-30

Research used current repository metadata, README/docs, licenses and implementation source. Nothing below substitutes upstream claims for this project's hardware validation. No Omarchy installation script, Apple SDK binary, or third-party app SDK code is copied into this repository.

| Reference | License reviewed | Maintenance snapshot | Decision |
|---|---|---|---|
| [omarchy-apple-dev](https://github.com/joshuaswarren/omarchy-apple-dev) | MIT | Checkout `79bda716bf207924efc25bce923bda261dc67837` | Reuse ideas: xtool/SwiftPM, explicit tailnet RemotePairing, receipts. Do not copy Arch/AUR/user-path setup or promise its custom patches are in upstream xtool |
| [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) | GPLv3 | Active; pushed 2026-10-29; research checkout `36193af87b86f18f6b3b0728fb7bc16aecaf8c9d`; installed/pinned PyPI 11.48.0 | Optional main device dependency. Protocol reimplementation would duplicate substantial pairing/RemoteXPC/HID work |
| [Appium WebDriverAgent](https://github.com/appium/WebDriverAgent) | BSD license text with 3 conditions; GitHub API says NOASSERTION | Active; pushed 2026-10-29 | Optional external HTTP service. Preserve upstream license if redistributing it; not bundled here |
| [appium-xcuitest-driver](https://github.com/appium/appium-xcuitest-driver) | Apache-2.0 | Active; pushed 2026-10-30 | Reference for physical XCTest/WDA provisioning/version constraints. Full Appium dependency unnecessary for the small HTTP adapter |
| [sentry-cocoa](https://github.com/getsentry/sentry-cocoa) | MIT | Active; pushed 2026-10-29 | Reference for bounded diagnostics/breadcrumbs and privacy controls. Not a device automation backend; no runtime dependency |
| [Instabug-iOS](https://github.com/Instabug/Instabug-iOS) | Restrictive: use as-is, modifications not allowed; not treated as permissive OSS | Archived 2025-10-09; now Luciq branding | Feedback UX reference only. No code, binaries or dependency integrated |
| [idb](https://github.com/meta/idb) (redirect from facebook/idb) | MIT | Active; pushed 2026-10-30 | Remote client/companion architecture reference. macOS companion and simulator-only features cannot establish native Linux physical-device support |
| [MobileBuildMCP](https://www.mobilebuildmcp.com/) / [source](https://github.com/getsentry/MobileBuildMCP) | MIT | Active; pushed 2026-10-27 | CLI/MCP parity and structured tool boundaries. Xcode-based implementation is not a Linux compiler backend |
| [xtool](https://github.com/xtool-org/xtool) | MIT | Active; pushed 2026-10-28; checkout `f1b455b4c52305fb073e44f191b01c9e9db19784` | Optional external build adapter. SwiftPM input, Darwin SDK compatibility, and signing remain explicit gates |
| [zsign](https://github.com/zhlynn/zsign) | MIT | Active; pushed 2026-10-20 | Optional external signing adapter; not installed or validated against an Apple identity here |

A repository's recent push is maintenance evidence, not a support guarantee. WDA's GitHub license classifier was not trusted in place of reading the actual LICENSE. The restrictive [Instabug license](https://github.com/Instabug/Instabug-iOS/blob/master/LICENSE.md) is why it is reference-only.

## Device findings that shape implementation

- [HID implementation](https://github.com/doronz88/pymobiledevice3/blob/36193af87b86f18f6b3b0728fb7bc16aecaf8c9d/pymobiledevice3/remote/core_device/hid_service.py): a running display-media session authenticates touch delivery. An acknowledged report alone can be dropped by the device. The adapter uses upstream `touch_session` and never equates transport success with application success.
- [CoreDevice CLI](https://github.com/doronz88/pymobiledevice3/blob/36193af87b86f18f6b3b0728fb7bc16aecaf8c9d/pymobiledevice3/cli/developer/core_device.py): coordinate normalization is 16-bit; touch drag differs from pointer swipe. The adapter generates CONTACT samples and RELEASE, with bounded durations.
- [Python API guide](https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/python-api.md): modern services are async, RSD is required for iOS 17+ developer access, userspace tunnel addresses are process-local, and only one userspace tunnel is allowed per process. MCP serializes device calls accordingly.
- [Tailnet report](https://github.com/joshuaswarren/omarchy-apple-dev/blob/79bda716bf207924efc25bce923bda261dc67837/docs/OVER-TAILNET.md): pairing/bootstrap, host identity, explicit remote ports, Wi-Fi and return routing matter. Tailscale is not a replacement for Apple services. Older reports may be superseded by newer upstream implementations; this toolkit requires its own receipts.

## Dependency rationale and redistribution

The Python toolkit is GPL-3.0-only to be compatible with its pymobiledevice3 integration. The independently authored Swift registry has its own MIT license and no pymobiledevice3 code/dependency. Pillow is used for reliable image decoding and actual pixel comparison; comparing PNG bytes would misinterpret encoding differences. The official MCP SDK handles protocol negotiation, validation and stdio. FFmpeg, xtool and zsign are optional external executables; their binaries are not vendored. FFmpeg build licensing varies by configuration and must be checked when distributing derived images.

The Docker image contains the Python device stack and therefore its transitive dependencies; retain required third-party notices/source obligations when distributing images. The lockfile is a dependency resolution artifact, not a representation that all optional native libraries were validated on every architecture. Proprietary Apple frameworks/SDKs and provisioning rights are separate from this repository's license.

## Capture research

Apple's current [ScreenCaptureKit documentation](https://developer.apple.com/documentation/screencapturekit) lists iOS/iPadOS 27+ availability. Its [iOS capture sample](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-on-ios) describes picker-based consent, `SCRecordingOutput`, and `SCClipBufferingOutput` for up to 15 seconds of rolling clips. These findings inform a later SDK milestone; no untested API shim is presented as working implementation. See [capture](../capture.md) for fallback/permission constraints.
