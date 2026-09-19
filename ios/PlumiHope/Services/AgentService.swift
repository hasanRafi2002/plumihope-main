import Foundation

struct AgentApplicationRequest: Encodable {
    let fullName: String
    let phone: String?
    let location: String?
    let experience: String?
    let facebookUrl: String?
    let youtubeUrl: String?
    let otherUrl: String?

    enum CodingKeys: String, CodingKey {
        case fullName = "full_name"
        case phone
        case location
        case experience
        case facebookUrl = "facebook_url"
        case youtubeUrl = "youtube_url"
        case otherUrl = "other_url"
    }
}

final class AgentService {
    static let shared = AgentService()
    private let client = APIClient.shared

    private init() {}

    func getMyAgentProfile() async throws -> AgentProfileDetail? {
        let endpoint = APIEndpoint(path: "/agents/me", method: .get, requiresAuth: true)
        return try await client.request(endpoint)
    }

    func applyAsAgent(
        fullName: String,
        phone: String?,
        location: String?,
        experience: String?,
        facebookUrl: String?,
        youtubeUrl: String?,
        otherUrl: String?
    ) async throws -> AgentProfileDetail {
        let body = AgentApplicationRequest(
            fullName: fullName,
            phone: phone,
            location: location,
            experience: experience,
            facebookUrl: facebookUrl,
            youtubeUrl: youtubeUrl,
            otherUrl: otherUrl
        )
        let endpoint = APIEndpoint(path: "/agents/apply", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: body)
    }
}
