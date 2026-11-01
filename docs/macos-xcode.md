# macOS development with Xcode and a physical iPhone

Use Xcode to build, sign, run, and distribute your iOS app. Run `remote-ios-agent` on the same Mac to capture screenshots, send UI actions, and collect diagnostics. Start with a USB-connected iPhone; remote networking can follow once the local loop works.

**Validation status:** the Python toolkit and Swift SDK registry have been tested on macOS. This repository has not yet verified the complete Xcode → physical iPhone → toolkit interaction loop. The steps below are a setup guide, not a hardware test receipt. See [validation evidence](validation.md).

## 1. Prepare the Mac and iPhone

- Install full [Xcode](https://developer.apple.com/xcode/) compatible with your Mac and the phone's iOS version. Launch it and finish the requested component installation. Command Line Tools alone do not supply the iOS development environment.
- Add your Apple Account in Xcode Settings → Apple Accounts (called Accounts in some versions).
- Connect an unlocked iPhone by USB and approve Trust on the phone. Enable Settings → Privacy & Security → Developer Mode, including the requested restart and confirmation. If the setting is absent, connect the device to Xcode first.
- Open Xcode's device management window (Device Hub, or Devices and Simulators in older versions) and let device preparation finish.

Apple documents [running on physical devices](https://developer.apple.com/documentation/xcode/running-your-app-on-simulated-or-physical-devices) and [enabling Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device). Menu labels vary by Xcode version.

A personal Apple Account can be used for personal device testing, subject to provisioning and capability restrictions. TestFlight and distribution to registered testers require Apple Developer Program membership. See Apple's [account overview](https://developer.apple.com/help/account/basics/about-your-developer-account) and [distribution guide](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases/).

## 2. Install the toolkit on macOS

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) using its official instructions. If you already use Homebrew, `brew install uv` is an option. Then, from your chosen workspace:

```sh
git clone https://github.com/harryworld/remote-ios-agent.git
cd remote-ios-agent
uv python install 3.12
uv sync --frozen --all-extras --python 3.12
uv run remote-ios doctor
```

Reuse an existing checkout instead of cloning over it. Run the remaining toolkit commands from this repository directory. The frozen sync installs the Python device, MCP, and development extras; it does not configure Xcode signing or phone access. Do not run `scripts/install-linux.sh` on macOS.

For this Xcode workflow, missing `xtool`, `zsign`, or `ld.lld` in the doctor output is expected. Xcode supplies the Apple build/signing path. FFmpeg is optional for sampled video; Tailscale is optional for remote networking. Neither is required for the initial USB workflow.

Check the installation without a phone:

```sh
uv run remote-ios --backend mock workflow run examples/agent-workflows/smoke.json
```

This is explicitly simulated. Its screenshots and results do not establish real device access.

## 3. Build and run with Xcode

Open your app's `.xcworkspace` if its setup requires one; otherwise open its `.xcodeproj`. In the app target's Signing & Capabilities settings, select your team, enable automatic signing, and set a unique bundle identifier. Select the app scheme and your physical iPhone as the run destination, then choose Product → Run. Resolve any provisioning errors Xcode reports before continuing. See Apple's [device run instructions](https://help.apple.com/xcode/mac/current/en.lproj/dev5a825a1ca.html).

For a small test app, create an **iOS App** project in Xcode with Swift and SwiftUI. Keep its generated app entry point and replace `ContentView.swift` with:

```swift
import SwiftUI
import OSLog

struct ContentView: View {
    @State private var count = 0
    private let logger = Logger(subsystem: "RemoteIOSCounter", category: "interaction")

    var body: some View {
        VStack(spacing: 24) {
            Text("Count: \(count)")
                .accessibilityIdentifier("counter-\(count)")
            Button("Increment") {
                count += 1
                logger.info("Counter changed to \(count)")
                print("Counter changed to \(count)")
            }
            .accessibilityIdentifier("increment")
        }
        .padding()
    }
}
```

Use the bundle identifier you configured in Xcode in all commands below. The repository's `examples/demo-ios-app` is a SwiftPM/xtool input, not a ready-made Xcode app project; the small Xcode app above avoids needing xtool.

`remote-ios build` currently invokes xtool and rejects `.xcodeproj`/`.xcworkspace` input, including on macOS. Use Xcode for this guide's builds. The optional SDK is unnecessary for screenshots or coordinate taps.

## 4. Select the real phone

Discover USB devices through the toolkit's dependency:

```sh
uv run pymobiledevice3 usbmux list
```

If Apple trust is not yet established for this client, deliberately pair with the actual UDID and approve any phone prompt:

```sh
uv run pymobiledevice3 lockdown pair --udid YOUR_DEVICE_UDID
```

Create or update the ignored `remote-ios.toml`, preserving any existing device entries. Replace the placeholder with the discovered UDID:

```toml
[remote_ios]
backend = "pmd3"
selected = "phone"
artifacts = "artifacts"
timeout = 30

[devices.phone]
identifier = "YOUR_DEVICE_UDID"
transport = "usb"
orientation = "portrait"
```

Keep the phone in the configured orientation, unlocked, with the test app visible. Then check:

```sh
uv run remote-ios --device phone device status
```

A configured device appearing in `devices list` is not a connection check. `device status` opens a scoped connection and checks services; it closes on exit. A separate command opens its own session. USB trust, compatible RSD developer services, and developer image preparation are still required. If Xcode can run the app but toolkit status fails, follow [device setup](device-setup.md) and record the actual error; do not switch silently to mock mode.

## 5. Observe, interact, and verify

After Xcode installs the development build, it can remain installed for repeated toolkit sessions. Stop Xcode's debug session before using toolkit launch/termination commands, then launch using your actual bundle ID:

```sh
uv run remote-ios --device phone launch com.yourcompany.CounterDemo
uv run remote-ios --device phone ui screenshot
```

Open the PNG path returned in the JSON response. Find the Increment button using **the original image's pixel coordinates**, not SwiftUI points or a scaled preview's coordinates. Replace `BUTTON_X` and `BUTTON_Y` below with those numeric values:

```sh
uv run remote-ios --device phone workflow interact-verify --x BUTTON_X --y BUTTON_Y --wait 1
uv run remote-ios --device phone logs com.yourcompany.CounterDemo --seconds 5
```

The workflow keeps before-capture, tap, wait, and after-capture in one session and returns artifact paths and comparison results. Inspect both images and confirm the counter increased by exactly one. Run the interaction a second time to check repeatability. Optionally add `--roi X,Y,WIDTH,HEIGHT` around the counter to reduce unrelated changes.

`dispatched` means the event was sent; pixel differences alone cannot prove that the intended button received it. Native HID availability depends on the phone's OS/services and authenticated media connection. WDA is optional for accessibility assertions; see [UI automation](ui-automation.md).

Logs are a bounded live capture, not historical Xcode console output. To capture an increment message, start the logs command with `--seconds 20` in a second terminal before the interaction. Empty results do not prove the app emitted no logs; use Xcode's console as an independent diagnostic source. Commands return JSON and nonzero exit status on failure. Keep captures, logs, and configuration private.

## 6. Export an IPA or distribute through TestFlight

Choose the delivery method that fits the recipient:

| Purpose | Xcode path | Toolkit role |
|---|---|---|
| Develop on your connected iPhone | Product → Run with automatic signing | Inspect/interact after installation |
| Install a development or registered-device build | Archive, then export a properly provisioned IPA | Install the exported IPA on the selected phone |
| Share with beta testers | Archive, upload to App Store Connect, distribute via TestFlight | No TestFlight upload or tester management implemented |

### Export for a registered device

Select an iOS **device** destination appropriate for the target, not an iOS Simulator archive. Choose Product → Archive. In Organizer, select the archive and choose Distribute App, then the development/debugging or registered-device release-testing option appropriate to your Xcode version. Export an IPA with the correct signing identity, bundle ID, entitlements, and target device included in its provisioning profile. See Apple's [registered-device distribution guide](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).

Install the exact exported file, substituting its path and your app's bundle ID:

```sh
uv run remote-ios --device phone install /path/to/export/CounterDemo.ipa
uv run remote-ios --device phone launch com.yourcompany.CounterDemo
```

Keep Xcode's exported signature intact; `remote-ios sign` is unnecessary here. An App Store distribution export is not a development/ad hoc IPA for direct installation. Expired profiles, missing device registration, or mismatched entitlements can prevent installation or launch.

### TestFlight

Use a developer-program team and an App Store Connect app record matching the bundle ID. Set the version/build, archive for iOS devices, and use Organizer's App Store Connect upload flow. After processing, configure testing in App Store Connect and invite testers; external testing may require Beta App Review. Testers install via the TestFlight app. Follow Apple's [beta distribution instructions](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases/) for the current flow.

TestFlight delivery does not grant pairing, HID, or debug access to a tester's phone. This guide's toolkit workflow still requires deliberate device setup. The optional RemoteIOSAgentSDK registry is disabled in Release builds; a typical TestFlight build will not enable it.

## 7. Add remote access or agent integration later

Once the local loop works, follow [device setup](device-setup.md) for RemotePairing/RSD and Tailscale routing. A Mac-hosted agent can use this same CLI or [MCP server](mcp.md). A Linux agent may receive a securely transferred, device-valid IPA built by Xcode on the Mac and install it using its own configured device connection. That is a Mac build workflow, not evidence of Linux compilation.

Tailscale does not replace Apple pairing or expose a USB phone automatically. The toolkit does not implement a Mac build-server daemon or a general remote Xcode adapter. Keep WDA and developer services off the public internet.

## Troubleshooting

| Symptom | Next check |
|---|---|
| Xcode cannot run on the phone | Unlock/trust, Developer Mode, Xcode/iOS compatibility, team, bundle ID, and signing errors |
| USB discovery returns `[]` | Data-capable cable, unlocked phone, trust prompt, and Xcode device visibility |
| Toolkit service/tunnel failure after Xcode succeeds | Actual error, compatible developer image, RSD availability, pairing, and [device setup](device-setup.md) |
| Screenshot succeeds but taps do nothing | Authenticated HID/media service, return route, configured orientation, and original screenshot pixels |
| IPA install fails | Export method, signature/profile validity, included UDID, entitlements, and minimum iOS version |
| `doctor` reports missing xtool/zsign | Expected when Xcode handles builds and signing; only install them for the separate xtool workflow |

Record the Mac/Xcode/iOS versions, transport, command results, and before/after evidence when validating this guide. Report simulated tests separately from physical-device outcomes.
