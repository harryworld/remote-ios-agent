import SwiftUI
import os

@main
struct RemoteIOSDemoApp: App {
    var body: some Scene {
        WindowGroup { CounterView() }
    }
}

struct CounterView: View {
    @State private var count = 0
    @State private var text = ""
    private let logger = Logger(subsystem: "com.example.RemoteIOSDemo", category: "interaction")

    var body: some View {
        VStack(spacing: 24) {
            Text("Remote iOS Demo").font(.largeTitle)
            Text("Count: \(count)")
                .font(.system(size: 60, weight: .bold, design: .monospaced))
                .accessibilityIdentifier("counter-\(count)")
            Button("Increment") {
                count += 1
                logger.notice("Counter changed to \(count, privacy: .public)")
                print("REMOTE_IOS_DEMO counter=\(count)")
            }
            .buttonStyle(.borderedProminent)
            .accessibilityIdentifier("increment")
            TextField("Type here", text: $text)
                .textFieldStyle(.roundedBorder)
                .accessibilityIdentifier("demo-text")
            Text("Use screenshot pixels; layout varies by device.")
                .font(.caption)
        }
        .padding(32)
    }
}
