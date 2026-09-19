import Foundation

struct AgentProfile: Codable, Identifiable {
    let id: UUID
    let userId: UUID
    let status: String
    let fullName: String
    let location: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case status
        case fullName = "full_name"
        case location
        case createdAt = "created_at"
    }
}


struct AgentProfileDetail: Codable, Identifiable {
    let id: UUID
    let userId: UUID
    let status: String
    let fullName: String
    let location: String?
    let createdAt: Date
    let phone: String?
    let experience: String?
    let facebookUrl: String?
    let youtubeUrl: String?
    let otherUrl: String?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case status
        case fullName = "full_name"
        case location
        case createdAt = "created_at"
        case phone
        case experience
        case facebookUrl = "facebook_url"
        case youtubeUrl = "youtube_url"
        case otherUrl = "other_url"
    }
}
