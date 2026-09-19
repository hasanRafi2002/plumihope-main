import Foundation
import Combine

@MainActor
final class AgentCasesViewModel: ObservableObject {
    @Published var available: [HelpRequestSummary] = []
    @Published var myCases: [HelpRequestDetail] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var claimingId: UUID?
    @Published var claimErrorMessage: String?

    private let service = HelpRequestService.shared

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let availableFetch = service.listAvailableHelpRequests()
            async let myCasesFetch = service.listMyCases()
            available = try await availableFetch
            myCases = try await myCasesFetch
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func claim(_ requestId: UUID) async {
        claimingId = requestId
        claimErrorMessage = nil
        defer { claimingId = nil }

        do {
            _ = try await service.claimHelpRequest(id: requestId)
            await load()
        } catch {
            claimErrorMessage = error.localizedDescription
        }
    }
}
