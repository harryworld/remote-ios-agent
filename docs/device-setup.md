# Device setup

## One-time physical preparation

1. Use an iPhone you control. Enable Developer Mode and restart/confirm as iOS requests.
2. Unlock it and connect it by USB to a trusted setup host. Approve the on-device Trust prompt. Linux USB pairing is supported by pymobiledevice3; a Mac is not intrinsically mandatory for this step.
3. Discover the actual UDID and pair deliberately:

```sh
pymobiledevice3 usbmux list
pymobiledevice3 lockdown pair --udid YOUR_UDID
pymobiledevice3 lockdown remotepairing --udid YOUR_UDID --pair
```

The second pairing command is the newer RemotePairing record over trusted lockdown, distinct from the first Trust pairing. Availability is iOS/service dependent. Consult the installed command's `--help` rather than assuming old wireless pairing can add a Linux host.

4. Prepare/mount the compatible personalized developer disk image if the required services are absent. Use `pymobiledevice3 mounter --help` and the device's actual OS/build. The toolkit does not silently download/mount an image or reboot the phone.
5. Install Tailscale on the phone and Linux host, connect Wi-Fi on the phone, and confirm routing. mDNS does not ordinarily traverse a tailnet; determine the actual RemotePairing address/port on its local network, then configure it explicitly.
6. Securely provision only the selected RemotePairing record on the intended host. Records are private credentials, typically under `~/.local/share/pymobiledevice3/remote_<UDID>.plist`; use mode 600. Preserve the original pairing host identifier when migrating records. The upstream reference needed `host_identifier` pinned to the pairing host before migration; do not regenerate the identifier on the destination or edit every record indiscriminately.

The repository neither discovers nor copies private records automatically. No pairing records, certificates, or real device identifiers belong in Git.

## Connection choices

Copy `examples/remote-ios.example.toml` to ignored `remote-ios.toml`, fill in actual identifiers, and choose:

- `usb`: existing lockdown trust; preferred no-root tunnel on supported OS versions.
- `rsd`: an already-running, routable RSD address/port; all advertised service ports and media return routes must work.
- `remote-pairing`: phone's tailnet/LAN address, explicit RemotePairing port, and preexisting record. Current adapter creates a kernel TUN; configure OS privileges deliberately. TCP/QUIC is explicit. Python/OpenSSL TLS-PSK limitations may require a different Python build or QUIC.

```sh
remote-ios --device phone device status
remote-ios --device phone device connect --hold 60
```

`status` opens the selected device, checks its actual UDID, and lists advertised services. It is not a durable daemon. A second command creates a new scoped connection. Use Python/workflows for sequential operations in one session. On failure: check Wi-Fi, unlock state, tunnel lifetime, pairing identity, Developer Mode and DDI. Do not repeatedly replay taps whose result is uncertain.

## Mac exceptions

- A Mac may perform initial trust/RemotePairing preparation if Linux cannot do so on that iOS version.
- Authorized SDK/signing preparation may use Xcode/macOS tools; Linux builds use the resulting authorized inputs. Apple credentials remain private.
- Optional WDA generally needs macOS/Xcode for building/signing/provisioning its XCTest runner. A running/preinstalled compatible runner can be controlled over the network from Linux; restart/launch support is version-dependent and is not automated here.
- Local validation during this implementation ran on macOS. It does not satisfy Linux remote-phone acceptance.

## Version evidence

The reference project's [tailnet report](https://github.com/joshuaswarren/omarchy-apple-dev/blob/main/docs/OVER-TAILNET.md) describes iOS 27.0.1 success after USB bootstrap, and failures with cellular-only connectivity or an idle dark screen. These are **upstream observations, not this repository's hardware tests**, and do not establish support for every iOS release. Treat iOS 26 wireless bootstrap and iOS 17.0–17.3 Linux tunnel differences as compatibility gates.
