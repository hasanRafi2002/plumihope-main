import Foundation

struct HelpRequestDetail: Codable, Identifiable {
    let id: UUID
    let userId: UUID
    let category: String
    let subcategory: String?
    let description: String
    let location: String?
    let status: String
    let createdAt: Date
    let contactInfo: String?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case category
        case subcategory
        case description
        case location
        case status
        case createdAt = "created_at"
        case contactInfo = "contact_info"
        case updatedAt = "updated_at"
    }
}

struct HelpRequestCreateRequest: Encodable {
    let category: String
    let subcategory: String?
    let description: String
    let location: String?
    let contactInfo: String?

    enum CodingKeys: String, CodingKey {
        case category
        case subcategory
        case description
        case location
        case contactInfo = "contact_info"
    }
}

final class HelpRequestService {
    static let shared = HelpRequestService()
    private let client = APIClient.shared

    private init() {}

    func createHelpRequest(
        category: String,
        subcategory: String?,
        description: String,
        location: String?,
        contactInfo: String?
    ) async throws -> HelpRequestDetail {
        let body = HelpRequestCreateRequest(
            category: category,
            subcategory: subcategory,
            description: description,
            location: location,
            contactInfo: contactInfo
        )
        let endpoint = APIEndpoint(path: "/help-requests", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: body)
    }

    func getHelpRequest(id: UUID) async throws -> HelpRequestDetail {
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func listMyHelpRequests() async throws -> [HelpRequestDetail] {
        let endpoint = APIEndpoint(path: "/help-requests/me", method: .get, requiresAuth: true)
        return try await client.request(endpoint)
    }

    func cancelHelpRequest(id: UUID) async throws -> HelpRequestDetail {
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/cancel", method: .post, requiresAuth: true)
        return try await client.request(endpoint)
    }
}
