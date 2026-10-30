# Physical-device UI automation

```sh
remote-ios --device phone ui screenshot
remote-ios --device phone ui tap --x 200 --y 400
remote-ios --device phone ui swipe --from 200,600 --to 200,200 --duration 0.6
remote-ios --device phone ui long-press --x 200 --y 400 --duration 1
remote-ios --device phone ui type 'Hello World'
remote-ios --device phone ui press home
remote-ios --device phone ui observe
```

All public coordinates are **pixels in the most recently observed, full-resolution screenshot**, not UIKit points, scaled browser pixels, or normalized HID values. The API obtains a fresh screenshot before a coordinate gesture to establish dimensions. Bounds and finite values are checked. It converts to 0..65535 native portrait HID space, with explicit rotation transforms. Orientation comes from configuration, not a claimed sensor reading: default portrait, or `--orientation landscape-left|landscape-right|portrait-upside-down`. Lock orientation while executing. A landscape/portrait dimension mismatch fails closed; 180-degree rotation cannot be detected from dimensions alone. Rotation transforms are unit-tested but not validated on hardware yet.

The backend uses `touch_session`, which opens CoreDevice display media before universal HID. Without that stream, iOS can acknowledge a report yet discard the touch. Reverse media connectivity is mandatory. This implementation uses touchscreen CONTACT/RELEASE for a swipe/drag; the upstream similarly named `swipe` CLI primitive is pointer-only and is deliberately not used for touch dragging.

Long press is a held contact followed by release. Cleanup attempts release even on cancellation. Native typing prevalidates the entire string, supports US-layout ASCII/newline/tab, and rejects unsupported Unicode before typing anything. A field must already have focus. Button support includes home, lock, volume up/down and mute; availability depends on iOS/services/device policy.

## Verify effects

```sh
remote-ios --device phone workflow interact-verify --x 200 --y 400 \
  --roi 80,300,230,150 --threshold 0.01
```

The ROI is `x,y,width,height`. Comparison uses normalized mean absolute RGB difference, not encoded PNG hashes. Identical screenshots fail the interact-verify CLI with `no_visual_change`; before/after files remain available. Pixel differences can come from animation or status-bar clocks. They never set `verified=true` by themselves. Use a region that contains the expected result, and a semantic condition where possible. Tune the threshold for the UI; screenshot comparison is not an accessibility assertion.

## Optional WDA

Build/sign/provision Appium WebDriverAgent's XCTest runner with an appropriate Apple team and compatible Xcode/iOS version. Start the runner using a validated method for that device, forward/route its HTTP port over a trusted connection, create a session, and put its existing URL/session ID in configuration. This repository does not install or start WDA automatically and does not require the Appium server.

```sh
remote-ios --device phone ui tree
remote-ios --device phone ui tap-id increment
remote-ios --device phone ui wait-id counter-1 --seconds 10
remote-ios --device phone workflow interact-verify --x 200 --y 400 --assert-identifier counter-1
```

The optional client calls standard WDA source, accessibility-id element, click and displayed endpoints. A positive displayed assertion supplies stronger UI evidence; it still depends on meaningful application identifiers. WDA URL configuration is not proof of a live compatible runner. XCTest signing, developer disk images, iOS 17+ tunnel requirements, reboots, profile expiry and background runner lifetime can all block it. Keep its unauthenticated HTTP endpoint inside your restricted tailnet/tunnel.
