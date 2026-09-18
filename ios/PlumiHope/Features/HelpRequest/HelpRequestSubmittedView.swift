import SwiftUI

struct HelpRequestSubmittedView: View {
    @ObservedObject var viewModel: HelpRequestFormViewModel
    var path: Binding<NavigationPath>

    var body: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.green)

            Text("Help request submitted")
                .font(.title2)
                .fontWeight(.bold)

            Text("Your request has been received. Eligible Agents may now investigate the case.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            if let request = viewModel.submittedRequest {
                Text("Request ID: \(request.id.uuidString.prefix(8))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Button("Done") {
                viewModel.reset()
                path.wrappedValue = NavigationPath()
            }
            .buttonStyle(.borderedProminent)
            .frame(maxWidth: .infinity)
        }
        .padding()
        .navigationBarBackButtonHidden(true)
    }
}
