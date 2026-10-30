// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "RemoteIOSDemo",
    platforms: [.iOS(.v17)],
    products: [.library(name: "RemoteIOSDemo", targets: ["Demo"])],
    targets: [.target(name: "Demo")]
)
