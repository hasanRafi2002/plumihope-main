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

struct HelpRequestEvent: Codable, Identifiable {
    let id: UUID
    let actorId: UUID?
    let eventType: String
    let notes: String?
    let occurredAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case actorId = "actor_id"
        case eventType = "event_type"
        case notes
        case occurredAt = "occurred_at"
    }
}

struct HelpRequestSummary: Codable, Identifiable {
    let id: UUID
    let userId: UUID
    let category: String
    let subcategory: String?
    let description: String
    let location: String?
    let status: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case category
        case subcategory
        case description
        case location
        case status
        case createdAt = "created_at"
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

    func listAvailableHelpRequests() async throws -> [HelpRequestSummary] {
        let endpoint = APIEndpoint(
            path: "/help-requests",
            method: .get,
            requiresAuth: false,
            queryItems: [URLQueryItem(name: "status", value: "AVAILABLE")]
        )
        return try await client.request(endpoint)
    }

    func listMyCases() async throws -> [HelpRequestDetail] {
        let endpoint = APIEndpoint(path: "/help-requests/agent/cases", method: .get, requiresAuth: true)
        return try await client.request(endpoint)
    }

    func claimHelpRequest(id: UUID) async throws -> HelpRequestDetail {
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/claim", method: .post, requiresAuth: true)
        return try await client.request(endpoint)
    }

    func startInvestigation(id: UUID) async throws -> HelpRequestDetail {
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/start-investigation", method: .post, requiresAuth: true)
        return try await client.request(endpoint)
    }

    func addInvestigationNote(id: UUID, notes: String) async throws -> HelpRequestDetail {
        struct Body: Encodable { let notes: String }
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/notes", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: Body(notes: notes))
    }

    func logEvidenceUploaded(id: UUID, mediaId: UUID, evidenceType: String) async throws -> HelpRequestDetail {
        struct Body: Encodable {
            let mediaId: UUID
            let evidenceType: String
            enum CodingKeys: String, CodingKey {
                case mediaId = "media_id"
                case evidenceType = "evidence_type"
            }
        }
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/evidence", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: Body(mediaId: mediaId, evidenceType: evidenceType))
    }

    func listEvents(id: UUID) async throws -> [HelpRequestEvent] {
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/events", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func submitEligibilityDecision(id: UUID, eligible: Bool, notes: String?) async throws -> HelpRequestDetail {
        struct Body: Encodable { let eligible: Bool; let notes: String? }
        let endpoint = APIEndpoint(path: "/help-requests/\(id.uuidString)/eligibility", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: Body(eligible: eligible, notes: notes))
    }
}
