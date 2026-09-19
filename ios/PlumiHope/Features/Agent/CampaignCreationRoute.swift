import Foundation

enum CampaignCreationRoute: Hashable {
    case create(HelpRequestDetail)
}

extension HelpRequestDetail: Hashable {
    static func == (lhs: HelpRequestDetail, rhs: HelpRequestDetail) -> Bool {
        lhs.id == rhs.id
    }
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}
