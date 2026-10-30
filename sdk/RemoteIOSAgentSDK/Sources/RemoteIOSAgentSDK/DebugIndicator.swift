#if canImport(SwiftUI)
import SwiftUI

/// Place in the app's development UI. The registry has no transport yet.
public struct RemoteIOSDebugIndicator: View {
    public init() {}
    public var body: some View {
        #if DEBUG
        if RemoteIOSAgent.isEnabled {
            Label("Remote iOS registry enabled (local only)", systemImage: "ladybug.fill")
                .font(.caption).padding(8)
                .background(.orange.opacity(0.2), in: Capsule())
                .accessibilityIdentifier("remote-ios-debug-indicator")
        }
        #endif
    }
}
#endif
