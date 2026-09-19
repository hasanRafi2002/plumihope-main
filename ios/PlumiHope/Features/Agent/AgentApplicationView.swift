import SwiftUI

struct AgentApplicationView: View {
    @StateObject private var viewModel = AgentApplicationViewModel()
    var onSubmitted: () -> Void

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text("Become a PlumiHope Agent")
                    .font(.title2)
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Text("Verification is required before you can investigate cases or create campaigns.")
                    .font(.footnote)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                field("Full name", $viewModel.fullName)
                field("Phone", $viewModel.phone)
                field("Location", $viewModel.location)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Humanitarian experience")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    TextEditor(text: $viewModel.experience)
                        .frame(height: 100)
                        .padding(8)
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                }

                field("Facebook profile", $viewModel.facebookUrl)
                field("YouTube channel", $viewModel.youtubeUrl)
                field("Other public profile", $viewModel.otherUrl)

                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundColor(.red)
                }

                Button {
                    Task {
                        await viewModel.submit()
                        if viewModel.submittedProfile != nil {
                            onSubmitted()
                        }
                    }
                } label: {
                    if viewModel.isSubmitting {
                        ProgressView().frame(maxWidth: .infinity)
                    } else {
                        Text("Submit application").frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isSubmitting)
            }
            .padding()
        }
        .navigationTitle("Agent Application")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func field(_ label: String, _ text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
            TextField(label, text: text)
                .textFieldStyle(.roundedBorder)
        }
    }
}
