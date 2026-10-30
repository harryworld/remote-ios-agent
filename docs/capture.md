# Capture and artifacts

CoreDevice screenshot capture returns PNG artifacts and sidecars with device ID, UTC timestamp, dimensions, configured orientation, method, application context, session/action IDs and simulation flag. App ID is caller context after launch, not foreground-app detection. Artifact directories use mode 700 and screenshots/JSON use mode 600. Never automatically publish real-device screenshots or logs; they may include private UI content.

```sh
remote-ios ui screenshot
remote-ios capture periodic --seconds 10 --interval 1
remote-ios capture record --seconds 5 --interval 1
remote-ios compare artifacts/baseline.png artifacts/current.png --roi 0,100,390,600
```

Periodic capture is bounded to 60 seconds and 120 frames. The implemented video mode requires FFmpeg and encodes a **sampled screenshot sequence** to H.264/MP4. Frame durations reflect capture timestamps. It does not capture audio or claim realtime screen recording. Geometry changes abort conversion while retaining original PNG evidence.

## Evaluated alternatives

- pymobiledevice3 CoreDevice screenshot: implemented via `ScreenCaptureService`.
- Legacy screenshotr / DVT screenshot: useful on other service combinations; fallback adapter not implemented. Missing CoreDevice service is reported as an error.
- CoreDevice display streaming: implemented by upstream; this toolkit uses it to authenticate HID, discarding media. Native recording needs verified packet reception, HEVC framing, RTP/RTCP handling and decoder behavior. Not inferred from successful screenshots.
- Native HEVC: experimental upstream; not wrapped as a validated recorder here.
- WDA MJPEG: possible when a signed/running WDA exposes its streaming endpoint. Not implemented as a capture backend yet.
- Continuous web/VNC viewer: upstream provides viewers, but this repository has no viewer and the core workflow requires none.

## Future in-app capture

Apple's [iOS ScreenCaptureKit sample](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-on-ios) documents iOS 27+/Xcode 27, system content-sharing picker, recording outputs, and `SCClipBufferingOutput` with up to 15 seconds of rolling video. The current API supports exporting recent clips without interrupting buffering. This is a planned SDK integration, not implemented code in 0.1.

Use the system picker/permission flow and `NSScreenCaptureUsageDescription`; background full-display capture has additional configuration. Respect exclusions and user-selected content. Do not increase a stream's queue depth as a substitute for rolling recording. For older supported OS versions, evaluate ReplayKit with user consent, app-owned screenshots, and bounded state/log breadcrumbs. If capture is unavailable or denied, feedback must explicitly omit media rather than simulate it. No automatic hidden screen recording is planned.
