import SwiftUI

struct AuthenticatedAsyncImage: View {
    let mediaId: UUID

    @State private var uiImage: UIImage?
    @State private var failed = false

    var body: some View {
        Group {
            if let uiImage = uiImage {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFill()
            } else if failed {
                Color(.systemGray5)
                    .overlay(Image(systemName: "exclamationmark.triangle").foregroundColor(.secondary))
            } else {
                Color(.systemGray6)
                    .overlay(ProgressView())
            }
        }
        .task {
            await load()
        }
    }

    private func load() async {
        guard uiImage == nil else { return }
        do {
            let endpoint = APIEndpoint(path: "/media/\(mediaId.uuidString)/content", method: .get)
            let data = try await APIClient.shared.requestRawData(endpoint)
            if let image = UIImage(data: data) {
                uiImage = image
            } else {
                failed = true
            }
        } catch {
            print("AuthenticatedAsyncImage failed for \(mediaId): \(error)")
            failed = true
        }
    }
}
