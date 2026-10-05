import Foundation
import Combine

@MainActor
final class CampaignManageViewModel: ObservableObject {
    let campaignId: UUID

    @Published var campaign: CampaignDetail?
    @Published var updates: [CampaignUpdatePublic] = []
    @Published var evidence: [CampaignEvidencePublic] = []
    @Published var isLoading = true
    @Published var errorMessage: String?

    @Published var updateContent: String = ""
    @Published var isPostingUpdate = false
    @Published var updateErrorMessage: String?

    @Published var isConfirmingDelivered = false
    @Published var confirmErrorMessage: String?

    @Published var proofDeliveryDate = Date()
    @Published var proofAmountDelivered: String = ""
    @Published var proofNotes: String = ""
    @Published var isSubmittingProof = false
    @Published var proofErrorMessage: String?
    @Published var proofMediaId: UUID?

    private let service = CampaignService.shared
    private let mediaService = MediaService.shared

    init(campaignId: UUID) {
        self.campaignId = campaignId
    }

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let campaignFetch = service.getCampaignDetail(id: campaignId)
            async let updatesFetch = service.listUpdates(campaignId: campaignId)
            async let evidenceFetch = service.listCampaignEvidence(campaignId: campaignId)
            campaign = try await campaignFetch
            updates = try await updatesFetch
            evidence = try await evidenceFetch
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func postUpdate() async {
        guard !updateContent.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isPostingUpdate = true
        updateErrorMessage = nil
        defer { isPostingUpdate = false }

        do {
            _ = try await service.postUpdate(campaignId: campaignId, content: updateContent)
            updateContent = ""
            updates = try await service.listUpdates(campaignId: campaignId)
        } catch {
            updateErrorMessage = error.localizedDescription
        }
    }

    func confirmDelivered() async {
        isConfirmingDelivered = true
        confirmErrorMessage = nil
        defer { isConfirmingDelivered = false }

        do {
            campaign = try await service.confirmAssistanceDelivered(campaignId: campaignId)
        } catch {
            confirmErrorMessage = error.localizedDescription
        }
    }

    func uploadProofMedia(data: Data, filename: String, mimeType: String) async {
        do {
            let media = try await mediaService.uploadMedia(fileData: data, filename: filename, mimeType: mimeType)
            proofMediaId = media.id
        } catch {
            proofErrorMessage = error.localizedDescription
        }
    }

    func submitProof() async -> Bool {
        guard let mediaId = proofMediaId else {
            proofErrorMessage = "Please attach a proof photo or document first."
            return false
        }
        guard Double(proofAmountDelivered) ?? 0 > 0 else {
            proofErrorMessage = "Amount delivered must be greater than 0."
            return false
        }
        isSubmittingProof = true
        proofErrorMessage = nil
        defer { isSubmittingProof = false }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: proofDeliveryDate)

        do {
            campaign = try await service.submitAssistanceProof(
                campaignId: campaignId,
                mediaId: mediaId,
                deliveryDate: dateString,
                amountDelivered: proofAmountDelivered,
                notes: proofNotes.isEmpty ? nil : proofNotes
            )
            return true
        } catch {
            proofErrorMessage = error.localizedDescription
            return false
        }
    }
}
