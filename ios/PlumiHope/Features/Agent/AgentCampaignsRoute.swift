import Foundation

enum AgentCampaignsRoute: Hashable {
    case myCampaigns
}

struct CampaignManageRoute: Hashable {
    let campaignId: UUID
}
