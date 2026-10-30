// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "RemoteIOSAgentSDK",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [.library(name: "RemoteIOSAgentSDK", targets: ["RemoteIOSAgentSDK"])],
    targets: [
        .target(name: "RemoteIOSAgentSDK"),
        .testTarget(name: "RemoteIOSAgentSDKTests", dependencies: ["RemoteIOSAgentSDK"])
    ]
)
