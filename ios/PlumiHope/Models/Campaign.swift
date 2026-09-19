import Foundation

struct Campaign: Codable, Identifiable {
    let id: UUID
    let title: String
    let description: String
    let categoryId: UUID
    let targetAmount: String
    let raisedAmount: String
    let currency: String
    let status: String
    let verificationStatus: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case categoryId = "category_id"
        case targetAmount = "target_amount"
        case raisedAmount = "raised_amount"
        case currency
        case status
        case verificationStatus = "verification_status"
        case createdAt = "created_at"
    }

    var targetAmountValue: Double { Double(targetAmount) ?? 0 }
    var raisedAmountValue: Double { Double(raisedAmount) ?? 0 }
    var progressPercent: Double {
        guard targetAmountValue > 0 else { return 0 }
        return min(raisedAmountValue / targetAmountValue, 1.0)
    }
}


struct CampaignCategory: Codable, Identifiable, Hashable {
    let id: UUID
    let name: String
    let parentId: UUID?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case parentId = "parent_id"
    }
}

struct CampaignDetail: Codable, Identifiable {
    let id: UUID
    let title: String
    let description: String
    let categoryId: UUID
    let targetAmount: String
    let raisedAmount: String
    let currency: String
    let status: String
    let verificationStatus: String
    let createdAt: Date
    let helpRequestId: UUID
    let agentProfileId: UUID
    let recipientName: String?
    let recipientRelationship: String?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case categoryId = "category_id"
        case targetAmount = "target_amount"
        case raisedAmount = "raised_amount"
        case currency
        case status
        case verificationStatus = "verification_status"
        case createdAt = "created_at"
        case helpRequestId = "help_request_id"
        case agentProfileId = "agent_profile_id"
        case recipientName = "recipient_name"
        case recipientRelationship = "recipient_relationship"
        case updatedAt = "updated_at"
    }
}

struct CampaignEvidencePublic: Codable, Identifiable {
    let id: UUID
    let campaignId: UUID
    let evidenceType: String
    let visibility: String
    let verificationStatus: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case campaignId = "campaign_id"
        case evidenceType = "evidence_type"
        case visibility
        case verificationStatus = "verification_status"
        case createdAt = "created_at"
    }
}
