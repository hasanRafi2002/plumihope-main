import Foundation
import Combine

@MainActor
final class CreateCampaignViewModel: ObservableObject {
    let helpRequest: HelpRequestDetail

    // Step 1: Basics + Recipient
    @Published var title: String = ""
    @Published var description: String = ""
    @Published var targetAmount: String = ""
    @Published var currency: String = "BDT"
    @Published var recipientName: String = ""
    @Published var recipientRelationship: String = ""
    @Published var categories: [CampaignCategory] = []
    @Published var selectedCategoryId: UUID?
    @Published var isLoadingCategories = false
    @Published var isCreating = false
    @Published var createErrorMessage: String?

    // Created campaign (after Step 1)
    @Published var campaign: CampaignDetail?

    // Step 2: Evidence
    @Published var evidenceItems: [CampaignEvidencePublic] = []
    @Published var isUploadingEvidence = false
    @Published var evidenceErrorMessage: String?

    // Step 3: Payout
    @Published var payoutDestinationRef: String = ""
    @Published var isSavingPayout = false
    @Published var payoutErrorMessage: String?
    @Published var payoutSaved = false

    // Step 4: Submit
    @Published var isSubmitting = false
    @Published var submitErrorMessage: String?
    @Published var submitted = false

    private let campaignService = CampaignService.shared
    private let mediaService = MediaService.shared

    init(helpRequest: HelpRequestDetail) {
        self.helpRequest = helpRequest
        self.title = "Help with \(helpRequest.category.capitalized.replacingOccurrences(of: "_", with: " "))"
    }

    func loadCategories() async {
        isLoadingCategories = true
        defer { isLoadingCategories = false }
        do {
            categories = try await campaignService.listCategories()
            if selectedCategoryId == nil {
                selectedCategoryId = categories.first?.id
            }
        } catch {
            createErrorMessage = error.localizedDescription
        }
    }

    var canCreate: Bool {
        !title.trimmingCharacters(in: .whitespaces).isEmpty
            && !description.trimmingCharacters(in: .whitespaces).isEmpty
            && Double(targetAmount) ?? 0 > 0
            && selectedCategoryId != nil
    }

    func createDraft() async {
        guard let categoryId = selectedCategoryId else { return }
        isCreating = true
        createErrorMessage = nil
        defer { isCreating = false }

        do {
            campaign = try await campaignService.createCampaign(
                helpRequestId: helpRequest.id,
                categoryId: categoryId,
                title: title,
                description: description,
                targetAmount: targetAmount,
                currency: currency,
                recipientName: recipientName.isEmpty ? nil : recipientName,
                recipientRelationship: recipientRelationship.isEmpty ? nil : recipientRelationship
            )
        } catch {
            createErrorMessage = error.localizedDescription
        }
    }

    func uploadEvidence(data: Data, filename: String, mimeType: String, evidenceType: String) async {
        guard let campaign = campaign else { return }
        isUploadingEvidence = true
        evidenceErrorMessage = nil
        defer { isUploadingEvidence = false }

        do {
            let media = try await mediaService.uploadMedia(fileData: data, filename: filename, mimeType: mimeType)
            let evidence = try await campaignService.addEvidence(campaignId: campaign.id, mediaId: media.id, evidenceType: evidenceType)
            evidenceItems.append(evidence)
        } catch {
            evidenceErrorMessage = error.localizedDescription
        }
    }

    func savePayout() async {
        guard let campaign = campaign else { return }
        guard !payoutDestinationRef.trimmingCharacters(in: .whitespaces).isEmpty else {
            payoutErrorMessage = "Payout destination can't be empty."
            return
        }
        isSavingPayout = true
        payoutErrorMessage = nil
        defer { isSavingPayout = false }

        do {
            _ = try await campaignService.setPayoutDestination(campaignId: campaign.id, payoutDestinationRef: payoutDestinationRef)
            payoutSaved = true
        } catch {
            payoutErrorMessage = error.localizedDescription
        }
    }

    func submit() async {
        guard let campaign = campaign else { return }
        isSubmitting = true
        submitErrorMessage = nil
        defer { isSubmitting = false }

        do {
            _ = try await campaignService.submitCampaign(campaignId: campaign.id)
            submitted = true
        } catch {
            submitErrorMessage = error.localizedDescription
        }
    }
}
