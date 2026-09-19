import SwiftUI

struct AgentWorkspaceView: View {
    @StateObject private var viewModel = AgentCasesViewModel()
    @State private var selectedTab: CasesTab = .available

    enum CasesTab: String, CaseIterable {
        case available = "Available"
        case myCases = "My Cases"
    }

    var body: some View {
        VStack(spacing: 0) {
            Picker("", selection: $selectedTab) {
                ForEach(CasesTab.allCases, id: \.self) { tab in
                    Text(tab.rawValue).tag(tab)
                }
            }
            .pickerStyle(.segmented)
            .padding()

            if let claimErrorMessage = viewModel.claimErrorMessage {
                Text(claimErrorMessage)
                    .font(.footnote)
                    .foregroundColor(.red)
                    .padding(.horizontal)
            }

            Group {
                if viewModel.isLoading && viewModel.available.isEmpty && viewModel.myCases.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let errorMessage = viewModel.errorMessage {
                    VStack(spacing: 12) {
                        Text("Couldn't load cases")
                            .font(.headline)
                        Text(errorMessage)
                            .font(.footnote)
                            .foregroundColor(.secondary)
                        Button("Try again") {
                            Task { await viewModel.load() }
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if selectedTab == .available {
                    availableList
                } else {
                    myCasesList
                }
            }
        }
        .navigationTitle("Agent Workspace")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }

    private var availableList: some View {
        Group {
            if viewModel.available.isEmpty {
                emptyState("No available requests", "Check back later for new cases.")
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.available) { request in
                            availableRow(request)
                        }
                    }
                    .padding()
                }
            }
        }
    }

    private var myCasesList: some View {
        Group {
            if viewModel.myCases.isEmpty {
                emptyState("No claimed cases yet", "Claim a request from Available to start investigating.")
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.myCases) { request in
                            caseRow(request)
                        }
                    }
                    .padding()
                }
            }
        }
    }

    private func availableRow(_ request: HelpRequestSummary) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(request.category.capitalized.replacingOccurrences(of: "_", with: " "))
                .font(.caption)
                .foregroundColor(.secondary)
            Text(request.description)
                .font(.body)
                .lineLimit(2)
            HStack {
                if let location = request.location {
                    Text(location)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
                Button {
                    Task { await viewModel.claim(request.id) }
                } label: {
                    if viewModel.claimingId == request.id {
                        ProgressView()
                    } else {
                        Text("Claim")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.claimingId != nil)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private func caseRow(_ request: HelpRequestDetail) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(request.category.capitalized.replacingOccurrences(of: "_", with: " "))
                .font(.caption)
                .foregroundColor(.secondary)
            Text(request.description)
                .font(.body)
                .lineLimit(2)
            Text("● " + request.status.capitalized.replacingOccurrences(of: "_", with: " "))
                .font(.caption)
                .fontWeight(.semibold)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private func emptyState(_ title: String, _ message: String) -> some View {
        VStack(spacing: 12) {
            Text(title)
                .font(.headline)
            Text(message)
                .font(.footnote)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
