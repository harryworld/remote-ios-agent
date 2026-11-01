# Linux builds and signing

For native Mac builds and distribution using an existing Xcode project, follow the [macOS + Xcode guide](macos-xcode.md). `remote-ios build` remains the xtool adapter on every host.

## Supported input

The current adapter invokes `xtool dev build --configuration debug|release` in a trusted project containing `Package.swift` and `xtool.yml`, then requires exactly one `.app` artifact. It does not invoke `xcodebuild`, and explicitly rejects `.xcodeproj`/`.xcworkspace` input.

[xtool](https://github.com/xtool-org/xtool) is MIT licensed and provides SwiftPM-based iOS app packaging and Darwin SDK tooling. We reuse that approach as an external tool, rather than copying the Omarchy installer. Install xtool using its official instructions and pin the revision/toolchain you validate. The reference's custom fork includes additional compatibility patches; upstream xtool is not assumed equivalent to that entire patched environment.

## Swift and SDK preparation

Get a Swift Linux toolchain for your actual distro/architecture from [swift.org](https://www.swift.org/install/linux/). `scripts/install-swift.sh` accepts an explicit official archive URL, independently verified SHA-256, and new installation directory. It does not choose an arbitrary latest toolchain or install over an existing one.

```sh
swift --version
swift sdk list
xtool --help
# Only with your authorized SDK source and applicable agreements reviewed:
./scripts/configure-sdk.sh /authorized/Xcode.xip /new/sdk-output
remote-ios doctor
remote-ios build examples/demo-ios-app
```

Apple SDKs are proprietary, not included under this repository's GPL/MIT licenses. Do not download SDKs from unauthorized mirrors or redistribute extracted SDKs in a public image. Availability of a technical extraction method is not a grant of rights to run or distribute it on another platform; review your applicable Apple agreement. This toolkit does not provide legal advice or claim blanket permission for Linux SDK usage.

Swift's standard library/package support on Linux does not automatically supply UIKit, SwiftUI, Objective-C interoperability, Apple binary dependencies, or Darwin system libraries. The Swift compiler, SDK Swift interfaces, linker and runtime must be compatible. Macros, asset catalogs, storyboards, SwiftData, resource packaging, entitlements, extensions and generated build phases each need separate validation. No universal Xcode project compatibility is promised.

The reference [xcodeproj2xtool adapter](https://github.com/joshuaswarren/omarchy-apple-dev/blob/main/tools/xcodeproj2xtool.py) is a useful conversion starting point. Run it separately at a reviewed revision, inspect generated target/resource settings, and supply the resulting SwiftPM/xtool directory. It is not vendored or silently invoked. Unsupported build phases must be implemented deliberately or kept on a macOS build path outside this toolkit.

## Signing and IPA

`remote-ios build` does not claim a device-valid signature. A physical device needs a matching certificate/private key, provisioning profile containing its UDID (for development/ad hoc), bundle ID and entitlements. Apple account eligibility and provisioning expiration apply.

```sh
remote-ios sign path/to/Demo.app --key /secure/signing-key.pem \
  --profile /secure/Demo.mobileprovision --output build/Demo.ipa
remote-ios install build/Demo.ipa
```

The optional signing adapter invokes externally installed [zsign](https://github.com/zhlynn/zsign) (MIT) with an unencrypted private-key input; no password is placed in a command line. It is experimental and was not executed with an Apple identity here. Prepare/validate the key/certificate format supported by your zsign version; keep its inputs private. Use a dedicated development identity and protected filesystem. Installation then checks the device's application lookup; a successful signer exit alone does not prove the phone will accept the app.

To package an **already signed** `.app` without altering its files:

```sh
remote-ios package path/to/Demo.app --output build/Demo.ipa
```

The packager preserves normal file modes, rejects symlinks requiring platform-specific treatment, and does not validate cryptographic signatures. Existing signed IPAs can be installed directly; the optional signing tool is unnecessary in that case.

A pure Swift package can be built with its configured Swift SDK using SwiftPM directly. That is distinct from producing a signed app bundle. The demo uses a single SwiftUI library product following xtool's template; Linux iOS compilation remains unverified until the configured toolchain/SDK is available.
