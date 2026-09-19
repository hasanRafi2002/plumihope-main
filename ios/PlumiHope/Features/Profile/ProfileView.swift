import SwiftUI

struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()
    @EnvironmentObject var authManager: AuthManager
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if viewModel.isLoading && viewModel.user == nil {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let errorMessage = viewModel.errorMessage {
                    VStack(spacing: 12) {
                        Text("Couldn't load profile")
                            .font(.headline)
                        Text(errorMessage)
                            .font(.footnote)
                            .foregroundColor(.secondary)
                        Button("Try again") {
                            Task { await viewModel.load() }
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let user = viewModel.user {
                    List {
                        Section {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(user.fullName)
                                    .font(.title3)
                                    .fontWeight(.semibold)
                                Text(user.email)
                                    .font(.footnote)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.vertical, 4)

                            Button {
                                path.append(ProfileRoute.editProfile)
                            } label: {
                                Text("Edit profile")
                            }
                        }

                        Section("Activity") {
                            Button {
                                path.append(ProfileRoute.notifications)
                            } label: {
                                Label("Notifications", systemImage: "bell")
                            }

                            Button {
                                path.append(ProfileRoute.myHelpRequests)
                            } label: {
                                Label("Help requests", systemImage: "hand.raised")
                            }

                            Button {
                                path.append(ProfileRoute.myDonations)
                            } label: {
                                Label("My donations", systemImage: "heart.text.square")
                            }
                        }

                        Section("Agent") {
                            if let agentProfile = viewModel.agentProfile {
                                HStack {
                                    Text(agentStatusLabel(agentProfile.status))
                                    Spacer()
                                    if agentProfile.status == "VERIFIED" {
                                        Image(systemName: "checkmark.seal.fill")
                                            .foregroundColor(.green)
                                    }
                                }

                                if agentProfile.status == "VERIFIED" {
                                    Button {
                                        path.append(ProfileRoute.agentWorkspace)
                                    } label: {
                                        Label("Agent Workspace", systemImage: "briefcase")
                                    }
                                } else if agentProfile.status == "SUSPENDED" {
                                    Text("Your Agent account is suspended. You cannot create new campaigns while suspended.")
                                        .font(.footnote)
                                        .foregroundColor(.secondary)
                                } else if agentProfile.status == "RESTRICTED" {
                                    Text("Some Agent capabilities are temporarily limited while a review is in progress.")
                                        .font(.footnote)
                                        .foregroundColor(.secondary)
                                } else if agentProfile.status == "REVOKED" {
                                    Text("Your Agent access has been revoked.")
                                        .font(.footnote)
                                        .foregroundColor(.secondary)
                                } else if agentProfile.status == "REJECTED" {
                                    Text("Your Agent application was not approved.")
                                        .font(.footnote)
                                        .foregroundColor(.secondary)
                                } else {
                                    Text("Your application is being reviewed.")
                                        .font(.footnote)
                                        .foregroundColor(.secondary)
                                }
                            } else {
                                Button {
                                    path.append(ProfileRoute.becomeAgent)
                                } label: {
                                    Label("Apply to become an Agent", systemImage: "person.badge.plus")
                                }
                            }
                        }

                        Section {
                            Button(role: .destructive) {
                                authManager.logout()
                            } label: {
                                Text("Sign out")
                            }
                        }
                    }
                }
            }
            .navigationTitle("Profile")
            .navigationDestination(for: ProfileRoute.self) { route in
                switch route {
                case .myHelpRequests:
                    MyHelpRequestsView(path: $path)
                case .myDonations:
                    MyDonationsView(path: $path)
                case .notifications:
                    NotificationsView()
                case .editProfile:
                    if let user = viewModel.user {
                        EditProfileView(user: user) {
                            Task { await viewModel.load() }
                        }
                    }
                case .becomeAgent:
                    AgentApplicationView {
                        if !path.isEmpty { path.removeLast() }
                        Task { await viewModel.load() }
                    }
                case .agentWorkspace:
                    AgentWorkspaceView()
                }
            }
            .navigationDestination(for: HelpRequestRoute.self) { route in
                switch route {
                case .status(let requestId):
                    HelpRequestStatusView(requestId: requestId)
                default:
                    EmptyView()
                }
            }
            .navigationDestination(for: MyDonationsRoute.self) { route in
                switch route {
                case .detail(let donationId):
                    DonationDetailLoaderView(donationId: donationId)
                }
            }
            .task {
                await viewModel.load()
            }
        }
    }

    private func agentStatusLabel(_ status: String) -> String {
        status.capitalized.replacingOccurrences(of: "_", with: " ")
    }
}

enum ProfileRoute: Hashable {
    case myHelpRequests
    case myDonations
    case notifications
    case editProfile
    case becomeAgent
    case agentWorkspace
}

#Preview {
    ProfileView()
        .environmentObject(AuthManager.shared)
}
