import Foundation
import Combine

@MainActor
final class ExploreViewModel: ObservableObject {
    @Published var campaigns: [Campaign] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var searchText: String = ""

    private let campaignService = CampaignService.shared
    private var latestRequestId = 0

    func loadCampaigns() async {
        latestRequestId += 1
        let requestId = latestRequestId
        isLoading = true
        errorMessage = nil

        let query = searchText.isEmpty ? nil : searchText
        let service = campaignService
        let work = Task { try await service.discover(query: query) }

        do {
            let result = try await work.value
            guard requestId == latestRequestId else { return }
            print("[Explore] loaded \(result.items.count) campaigns, raised: \(result.items.map { $0.raisedAmount })")
            campaigns = result.items
        } catch {
            guard requestId == latestRequestId else { return }
            print("[Explore] load failed: \(error)")
            errorMessage = error.localizedDescription
        }
        if requestId == latestRequestId { isLoading = false }
    }
}
