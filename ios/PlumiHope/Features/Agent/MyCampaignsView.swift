import SwiftUI

struct MyCampaignsView: View {
    @StateObject private var viewModel = MyCampaignsViewModel()
    var path: Binding<NavigationPath>

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.campaigns.isEmpty {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.campaigns.isEmpty {
                VStack(spacing: 12) {
                    Text("No campaigns yet")
                        .font(.headline)
                    Text("Campaigns you create will appear here.")
                        .font(.footnote)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.campaigns) { campaign in
                            Button {
                                path.wrappedValue.append(CampaignManageRoute(campaignId: campaign.id))
                            } label: {
                                row(campaign)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("My Campaigns")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }

    private func row(_ campaign: CampaignDetail) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(campaign.title)
                .font(.body)
                .fontWeight(.semibold)
            Text("● " + campaign.status.capitalized.replacingOccurrences(of: "_", with: " "))
                .font(.caption)
                .fontWeight(.semibold)
            Text("\(campaign.raisedAmount) / \(campaign.targetAmount) \(campaign.currency)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}
