import Foundation

public enum AgentError: Error, Equatable {
    case disabled, unknownAction, duplicateAction, invalidName
}

public struct EmptyArguments: Codable, Sendable {
    public init() {}
}

public struct EmptyResult: Codable, Sendable {
    public init() {}
}

/// Local registry foundation. No network listener, filesystem API, reflection or code evaluator.
/// A future authenticated transport must authorize requests before calling `perform`.
@MainActor
public enum RemoteIOSAgent {
    private static var optedIn = false
    private static var actions: [String: (Data) async throws -> Data] = [:]
    private static var providers: [String: () throws -> Data] = [:]
    private static var recentEvents: [DiagnosticEvent] = []
    public static var redactor: (String) -> String = { _ in "[redacted: configure a development redactor]" }

    public static var isEnabled: Bool {
        #if DEBUG
        optedIn
        #else
        false
        #endif
    }

    /// Must be called explicitly by development-only application code.
    public static func enableForDevelopment() {
        #if DEBUG
        optedIn = true
        #endif
    }

    public static func disable() {
        optedIn = false
        actions.removeAll()
        providers.removeAll()
        recentEvents.removeAll()
    }

    public static func register(_ name: String, action: @escaping @MainActor () async throws -> Void) throws {
        try register(name, arguments: EmptyArguments.self, result: EmptyResult.self) { _ in
            try await action()
            return EmptyResult()
        }
    }

    public static func register<Arguments: Decodable, Result: Encodable>(
        _ name: String, arguments: Arguments.Type, result: Result.Type,
        action: @escaping @MainActor (Arguments) async throws -> Result
    ) throws {
        guard isEnabled else { throw AgentError.disabled }
        guard !name.isEmpty, name.count <= 128 else { throw AgentError.invalidName }
        guard actions[name] == nil else { throw AgentError.duplicateAction }
        actions[name] = { data in
            let arguments = try JSONDecoder().decode(Arguments.self, from: data)
            let result = try await action(arguments)
            return try JSONEncoder().encode(result)
        }
    }

    public static func registerState<State: Encodable>(
        _ name: String, provider: @escaping @MainActor () throws -> State
    ) throws {
        guard isEnabled else { throw AgentError.disabled }
        guard !name.isEmpty, name.count <= 128 else { throw AgentError.invalidName }
        providers[name] = { try JSONEncoder().encode(provider()) }
    }

    public static var capabilities: [String] { isEnabled ? actions.keys.sorted() : [] }

    public static func perform(_ name: String, arguments: Data = Data("{}".utf8)) async throws -> Data {
        guard isEnabled else { throw AgentError.disabled }
        guard let action = actions[name] else { throw AgentError.unknownAction }
        let result = try await action(arguments)
        record(category: "action", message: name)
        return result
    }

    /// Providers must return allowlisted non-sensitive state. State is never sent automatically.
    public static func state() throws -> [String: Data] {
        guard isEnabled else { throw AgentError.disabled }
        return try providers.mapValues { try $0() }
    }

    public struct DiagnosticEvent: Codable, Sendable {
        public let timestamp: Date
        public let category: String
        public let message: String
    }

    public static func record(category: String, message: String) {
        guard isEnabled else { return }
        recentEvents.append(.init(timestamp: Date(), category: redactor(category), message: redactor(message)))
        if recentEvents.count > 200 { recentEvents.removeFirst(recentEvents.count - 200) }
    }

    public static var diagnostics: [DiagnosticEvent] { isEnabled ? recentEvents : [] }
}
