# Optional RemoteIOSAgentSDK

The Swift Package under `sdk/RemoteIOSAgentSDK` is MIT licensed independently from the Python GPL toolkit. The current implementation is a **local registry foundation**, not a remote debugging transport. It is off by default and remains disabled in release builds even if `enableForDevelopment()` is called.

```swift
#if DEBUG
RemoteIOSAgent.enableForDevelopment()
try RemoteIOSAgent.register("planner.openTaskEditor") {
    await planner.openTaskEditor()
}
struct OpenTask: Codable { let taskID: String }
struct ActionResult: Codable { let opened: Bool }
try RemoteIOSAgent.register("planner.openTask", arguments: OpenTask.self, result: ActionResult.self) { args in
    await planner.openTask(args.taskID)
    return ActionResult(opened: true)
}
try RemoteIOSAgent.registerState("navigation") {
    NavigationSnapshot(route: planner.route, loading: planner.isLoading)
}
#endif
```

Providers must supply explicitly allowlisted, non-sensitive Codable state. There is no private SwiftUI introspection, arbitrary Swift evaluation, or filesystem capability. Action execution is main-actor isolated and supports typed decoded arguments, encoded results, and thrown errors. Duplicate registration is rejected. `disable()` clears actions, providers, and diagnostics. A bounded 200-event local diagnostic ring redacts all strings by default until the developer supplies an appropriate redactor.

Place `RemoteIOSDebugIndicator()` in development UI after enabling. It explicitly says the registry is local only. It is not an indicator of a remote session (there is no transport yet). State/results are not automatically redacted or sent: the app owns its allowlist and must never put secrets in exported values.

## Next transport milestone (not implemented)

The intended app-initiated WebSocket connection is outbound to a private cloud broker. Before implementation acceptance, require:

- WSS with server authentication; short-lived per-app credentials, explicit local opt-in and authorization scopes.
- JSON version, request ID, capability list, arguments, result/error envelopes, and bounded payloads.
- Correlation, per-request deadlines, duplicate-ID rejection and replay protection; never replay non-idempotent actions on reconnect.
- Bounded reconnect backoff, disconnect/foreground lifecycle handling, and a visible active-session indicator.
- Allowlisted state, action names and diagnostic metadata; redaction before leaving the app.
- Feedback bundle schema with user-reviewed comments, build info, logs, state, recent actions, optional screenshot/video and explicit capture exclusions.
- A development-only SwiftUI feedback interface with preview/consent and redaction controls.

MCP SDK/feedback tools intentionally report unavailable until that broker and transport are implemented and tested. See [capture research](capture.md) for ScreenCaptureKit iOS 27 rolling clips and older-OS fallback requirements. No feedback upload, network interception, screen recording, or cloud connection occurs in this version.
