import Foundation
import Combine

@MainActor
final class MyCampaignsViewModel: ObservableObject {
    @Published var campaigns: [CampaignDetail] = []
    @Published var isLoading = true
    @Published var errorMessage: String?

    private let service = CampaignService.shared

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            campaigns = try await service.listMyCampaigns()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
