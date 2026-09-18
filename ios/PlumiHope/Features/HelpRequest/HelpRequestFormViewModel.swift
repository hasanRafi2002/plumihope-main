import Foundation
import Combine

@MainActor
final class HelpRequestFormViewModel: ObservableObject {
    @Published var category: String = ""
    @Published var subcategory: String = ""
    @Published var description: String = ""
    @Published var location: String = ""
    @Published var contactInfo: String = ""

    @Published var isSubmitting: Bool = false
    @Published var errorMessage: String?
    @Published var submittedRequest: HelpRequestDetail?

    private let service = HelpRequestService.shared

    let categories: [String] = [
        "MEDICAL", "EDUCATION", "EMERGENCY", "LIVELIHOOD",
        "DISASTER_RELIEF", "FOOD", "HOUSING", "DISABILITY", "COMMUNITY_SUPPORT", "OTHER",
    ]

    func submit() async {
        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }

        do {
            submittedRequest = try await service.createHelpRequest(
                category: category,
                subcategory: subcategory.isEmpty ? nil : subcategory,
                description: description,
                location: location.isEmpty ? nil : location,
                contactInfo: contactInfo.isEmpty ? nil : contactInfo
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func reset() {
        category = ""
        subcategory = ""
        description = ""
        location = ""
        contactInfo = ""
        isSubmitting = false
        errorMessage = nil
        submittedRequest = nil
    }
}
