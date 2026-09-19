import Foundation

struct MediaPublic: Codable, Identifiable {
    let id: UUID
    let mimeType: String
    let sizeBytes: Int
    let visibility: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case mimeType = "mime_type"
        case sizeBytes = "size_bytes"
        case visibility
        case createdAt = "created_at"
    }
}
