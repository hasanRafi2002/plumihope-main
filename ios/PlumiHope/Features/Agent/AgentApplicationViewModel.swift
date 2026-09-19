import Foundation
import Combine

@MainActor
final class AgentApplicationViewModel: ObservableObject {
    @Published var fullName: String = ""
    @Published var phone: String = ""
    @Published var location: String = ""
    @Published var experience: String = ""
    @Published var facebookUrl: String = ""
    @Published var youtubeUrl: String = ""
    @Published var otherUrl: String = ""

    @Published var isSubmitting: Bool = false
    @Published var errorMessage: String?
    @Published var submittedProfile: AgentProfileDetail?

    private let service = AgentService.shared

    func submit() async {
        guard !fullName.trimmingCharacters(in: .whitespaces).isEmpty else {
            errorMessage = "Full name can't be empty."
            return
        }
        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }

        do {
            submittedProfile = try await service.applyAsAgent(
                fullName: fullName,
                phone: phone.isEmpty ? nil : phone,
                location: location.isEmpty ? nil : location,
                experience: experience.isEmpty ? nil : experience,
                facebookUrl: facebookUrl.isEmpty ? nil : facebookUrl,
                youtubeUrl: youtubeUrl.isEmpty ? nil : youtubeUrl,
                otherUrl: otherUrl.isEmpty ? nil : otherUrl
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
