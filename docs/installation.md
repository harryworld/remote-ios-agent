# Installation

## macOS with Xcode

Follow the [macOS + Xcode guide](macos-xcode.md) for native Xcode builds, signing, physical-iPhone deployment, toolkit setup, and TestFlight distribution. The Linux installer below is not used on macOS.

## Ubuntu/Debian

Use Python 3.12+ (Ubuntu 24.04 includes 3.12). On older Debian releases, install a supported Python explicitly rather than replacing the system interpreter. Both x86_64 and ARM64 are CI targets, subject to upstream package wheels/system libraries.

```sh
sudo apt-get update
sudo apt-get install python3-venv python3-dev build-essential pkg-config libusb-1.0-0 usbmuxd
python3 --version
./scripts/install-linux.sh
source .venv/bin/activate
remote-ios doctor
```

The installer creates a user-owned venv, installs optional device/MCP dependencies, and prints the environment check. It does not install a desktop, modify shell startup, enroll Tailscale, or accept Apple agreements. The base Python package requires only Pillow for image decoding/comparison; `[device]`, `[mcp]`, and `[dev]` are isolated extras.

For a reproducible development environment use `uv sync --frozen --all-extras`; `uv.lock` contains resolved versions and hashes. `pip install -e '.[device,mcp]'` pins direct dependencies but permits transitive resolution. Review upstream fixes before deliberately updating the lock.

Install Tailscale through its [official distribution instructions](https://tailscale.com/download/linux), sign the host and phone into your own tailnet, and restrict connectivity with tailnet ACLs. Do not put auth keys in this repository. Install `ffmpeg` only if sampled video is needed.

## Docker

```sh
docker build -t remote-ios-agent .
docker run --rm remote-ios-agent doctor
docker run --rm -v "$PWD/artifacts:/home/agent/artifacts" remote-ios-agent \
  --backend mock workflow interact-verify --x 200 --y 400
```

The image installs from the frozen `uv.lock` with uv 0.9.7. It is headless, non-root, and excludes local configuration, certificates, pairing records, artifacts, and source-control metadata. Match writable artifact-directory permissions to container UID 10001. It does not contain Apple SDKs, xtool, Swift, signing credentials, or FFmpeg. Add those explicitly to a private derived image as needed.

For real RSD access on a Linux host, use host networking or explicitly routed tunnel networks. Mount only the selected pairing/configuration material read-only. Direct kernel RemotePairing requires `/dev/net/tun` and `NET_ADMIN`; the default unprivileged container intentionally cannot create that tunnel. Prefer creating the tunnel on the Linux host and connecting to its routable RSD endpoint. Docker Desktop networking is different; a successful mock container is not evidence of device connectivity. Never publish an unauthenticated tunnel/WDA endpoint to the public internet.

## Other hosts

The core package works without Linux-specific paths. macOS is useful for preparation/diagnosis but its native tunnel fallback does not establish Linux compatibility. Windows is not a validated target. Python 3.12 is the minimum; direct TCP RemotePairing requires compatible TLS-PSK support, which varies with the Python/OpenSSL build. The QUIC choice is explicit in configuration.
