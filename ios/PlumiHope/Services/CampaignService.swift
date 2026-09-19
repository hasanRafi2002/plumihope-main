import Foundation

struct PaginatedCampaigns: Codable {
    let items: [Campaign]
    let page: Int
    let pageSize: Int
    let total: Int
    let hasNext: Bool

    enum CodingKeys: String, CodingKey {
        case items
        case page
        case pageSize = "page_size"
        case total
        case hasNext = "has_next"
    }
}

struct WhyVerified: Codable {
    let agentIdentityReviewed: Bool
    let caseInvestigated: Bool
    let evidenceReviewed: Bool
    let campaignModeratorApproved: Bool
    let lastReviewedAt: Date?
    let disclaimer: String

    enum CodingKeys: String, CodingKey {
        case agentIdentityReviewed = "agent_identity_reviewed"
        case caseInvestigated = "case_investigated"
        case evidenceReviewed = "evidence_reviewed"
        case campaignModeratorApproved = "campaign_moderator_approved"
        case lastReviewedAt = "last_reviewed_at"
        case disclaimer
    }
}

struct CampaignCreateRequest: Encodable {
    let helpRequestId: UUID
    let categoryId: UUID
    let title: String
    let description: String
    let targetAmount: String
    let currency: String
    let recipientName: String?
    let recipientRelationship: String?

    enum CodingKeys: String, CodingKey {
        case helpRequestId = "help_request_id"
        case categoryId = "category_id"
        case title
        case description
        case targetAmount = "target_amount"
        case currency
        case recipientName = "recipient_name"
        case recipientRelationship = "recipient_relationship"
    }
}

struct CampaignUpdateRequestBody: Encodable {
    let payoutDestinationRef: String?

    enum CodingKeys: String, CodingKey {
        case payoutDestinationRef = "payout_destination_ref"
    }
}

struct CampaignEvidenceCreateRequest: Encodable {
    let mediaId: UUID
    let evidenceType: String
    let visibility: String

    enum CodingKeys: String, CodingKey {
        case mediaId = "media_id"
        case evidenceType = "evidence_type"
        case visibility
    }
}

final class CampaignService {
    static let shared = CampaignService()
    private let client = APIClient.shared

    private init() {}

    func discover(query: String? = nil, page: Int = 1) async throws -> PaginatedCampaigns {
        var items: [URLQueryItem] = [URLQueryItem(name: "page", value: String(page))]
        if let query = query, !query.isEmpty {
            items.append(URLQueryItem(name: "q", value: query))
        }
        let endpoint = APIEndpoint(path: "/campaigns/discover", method: .get, requiresAuth: false, queryItems: items)
        return try await client.request(endpoint)
    }

    func getCampaign(id: UUID) async throws -> Campaign {
        let endpoint = APIEndpoint(path: "/campaigns/\(id.uuidString)", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func getWhyVerified(campaignId: UUID) async throws -> WhyVerified {
        let endpoint = APIEndpoint(path: "/campaigns/\(campaignId.uuidString)/why-verified", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func listCategories() async throws -> [CampaignCategory] {
        let endpoint = APIEndpoint(path: "/campaigns/categories", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func createCampaign(
        helpRequestId: UUID,
        categoryId: UUID,
        title: String,
        description: String,
        targetAmount: String,
        currency: String,
        recipientName: String?,
        recipientRelationship: String?
    ) async throws -> CampaignDetail {
        let body = CampaignCreateRequest(
            helpRequestId: helpRequestId,
            categoryId: categoryId,
            title: title,
            description: description,
            targetAmount: targetAmount,
            currency: currency,
            recipientName: recipientName,
            recipientRelationship: recipientRelationship
        )
        let endpoint = APIEndpoint(path: "/campaigns", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: body)
    }

    func setPayoutDestination(campaignId: UUID, payoutDestinationRef: String) async throws -> CampaignDetail {
        let body = CampaignUpdateRequestBody(payoutDestinationRef: payoutDestinationRef)
        let endpoint = APIEndpoint(path: "/campaigns/\(campaignId.uuidString)", method: .patch, requiresAuth: true)
        return try await client.request(endpoint, body: body)
    }

    func addEvidence(campaignId: UUID, mediaId: UUID, evidenceType: String, visibility: String = "RESTRICTED") async throws -> CampaignEvidencePublic {
        let body = CampaignEvidenceCreateRequest(mediaId: mediaId, evidenceType: evidenceType, visibility: visibility)
        let endpoint = APIEndpoint(path: "/campaigns/\(campaignId.uuidString)/evidence", method: .post, requiresAuth: true)
        return try await client.request(endpoint, body: body)
    }

    func listCampaignEvidence(campaignId: UUID) async throws -> [CampaignEvidencePublic] {
        let endpoint = APIEndpoint(path: "/campaigns/\(campaignId.uuidString)/evidence", method: .get, requiresAuth: false)
        return try await client.request(endpoint)
    }

    func submitCampaign(campaignId: UUID) async throws -> CampaignDetail {
        let endpoint = APIEndpoint(path: "/campaigns/\(campaignId.uuidString)/submit", method: .post, requiresAuth: true)
        return try await client.request(endpoint)
    }
}
