import Foundation
import Combine

@MainActor
final class ProfileViewModel: ObservableObject {
    @Published var user: User?
    @Published var agentProfile: AgentProfileDetail?
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?

    private let service = UserService.shared
    private let agentService = AgentService.shared

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            user = try await service.getMyProfile()
        } catch {
            errorMessage = error.localizedDescription
        }

        agentProfile = try? await agentService.getMyAgentProfile()
    }
}
