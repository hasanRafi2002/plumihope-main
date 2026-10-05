import SwiftUI

struct CampaignCard: View {
    let campaign: Campaign

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Group {
                if let coverId = campaign.coverMediaId {
                    AuthenticatedAsyncImage(mediaId: coverId)
                } else {
                    Color(.systemGray5)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: 140)
            .clipShape(RoundedRectangle(cornerRadius: 12))

            Text("✓ Verified Case")
                .font(.caption)
                .foregroundColor(.green)

            Text(campaign.title)
                .font(.headline)
                .lineLimit(2)

            VStack(alignment: .leading, spacing: 4) {
                Text("\(formattedAmount(campaign.raisedAmountValue)) raised of \(formattedAmount(campaign.targetAmountValue))")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                ProgressView(value: campaign.progressPercent)
                    .tint(.green)
            }

            Text(campaign.status.capitalized.replacingOccurrences(of: "_", with: " "))
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(12)
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(.systemGray4), lineWidth: 1)
        )
    }

    private func formattedAmount(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 0
        formatter.groupingSeparator = ","
        return "৳" + (formatter.string(from: NSNumber(value: value)) ?? "0")
    }
}

#Preview {
    CampaignCard(campaign: Campaign(
        id: UUID(), title: "Help fund school fees", description: "desc",
        categoryId: UUID(), targetAmount: "50000", raisedAmount: "1000",
        currency: "BDT", status: "ACTIVE", verificationStatus: "UNVERIFIED",
        createdAt: Date()
    ))
    .padding()
}
