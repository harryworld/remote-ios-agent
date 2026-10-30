import XCTest
@testable import RemoteIOSAgentSDK

final class RegistryTests: XCTestCase {
    @MainActor
    func testOptInTypedActionAndDisable() async throws {
        RemoteIOSAgent.disable()
        XCTAssertFalse(RemoteIOSAgent.isEnabled)
        struct Args: Codable { let count: Int }
        RemoteIOSAgent.enableForDevelopment()
        #if DEBUG
        try RemoteIOSAgent.register("demo.double", arguments: Args.self, result: Int.self) { $0.count * 2 }
        let output = try await RemoteIOSAgent.perform("demo.double", arguments: Data("{\"count\":4}".utf8))
        XCTAssertEqual(try JSONDecoder().decode(Int.self, from: output), 8)
        XCTAssertEqual(RemoteIOSAgent.capabilities, ["demo.double"])
        XCTAssertThrowsError(try RemoteIOSAgent.register("demo.double") {})
        RemoteIOSAgent.record(category: "network", message: "secret")
        XCTAssertFalse(RemoteIOSAgent.diagnostics.last!.message.contains("secret"))
        #else
        XCTAssertFalse(RemoteIOSAgent.isEnabled)
        #endif
        RemoteIOSAgent.disable()
        XCTAssertTrue(RemoteIOSAgent.capabilities.isEmpty)
        do {
            _ = try await RemoteIOSAgent.perform("demo.double")
            XCTFail("Disabled registry executed action")
        } catch AgentError.disabled {}
    }
}
