import SwiftUI
import PhotosUI

struct CampaignManageView: View {
    @StateObject private var viewModel: CampaignManageViewModel
    @State private var photoItem: PhotosPickerItem?
    @State private var proofPhotoItem: PhotosPickerItem?
    @State private var showConfirmDeliveredDialog = false

    init(campaignId: UUID) {
        _viewModel = StateObject(wrappedValue: CampaignManageViewModel(campaignId: campaignId))
    }

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.campaign == nil {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let campaign = viewModel.campaign {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        Text(campaign.title)
                            .font(.title2)
                            .fontWeight(.bold)

                        Text("● " + campaign.status.capitalized.replacingOccurrences(of: "_", with: " "))
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        Text("\(campaign.raisedAmount) / \(campaign.targetAmount) \(campaign.currency)")
                            .font(.footnote)
                            .foregroundColor(.secondary)

                        Divider()

                        if campaign.status == "ACTIVE" || campaign.status == "TARGET_REACHED" {
                            postUpdateSection
                            Divider()
                        }

                        if campaign.status == "ASSISTANCE_PENDING" {
                            confirmDeliveredSection
                            Divider()
                        }

                        if campaign.status == "ASSISTANCE_DELIVERED" {
                            submitProofSection
                            Divider()
                        }

                        if campaign.status == "FINAL_REVIEW" {
                            finalReviewSection
                            Divider()
                        }

                        if campaign.status == "SUCCESSFUL" {
                            successfulSection
                            Divider()
                        }

                        Text("EVIDENCE")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        if viewModel.evidence.isEmpty {
                            Text("No evidence uploaded yet.")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                        } else {
                            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                                ForEach(viewModel.evidence) { item in
                                    VStack(alignment: .leading, spacing: 4) {
                                        if let mediaId = item.mediaId {
                                            AuthenticatedAsyncImage(mediaId: mediaId)
                                                .frame(height: 120)
                                                .clipped()
                                                .cornerRadius(8)
                                        }
                                        Text(item.evidenceType.capitalized.replacingOccurrences(of: "_", with: " "))
                                            .font(.caption2)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }

                        Divider()

                        Text("UPDATES")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        if viewModel.updates.isEmpty {
                            Text("No updates posted yet.")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                        } else {
                            ForEach(viewModel.updates) { update in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(update.content)
                                        .font(.subheadline)
                                    Text(update.createdAt.formatted(date: .abbreviated, time: .shortened))
                                        .font(.caption2)
                                        .foregroundColor(.secondary)
                                }
                                .padding()
                                .background(Color(.systemGray6))
                                .cornerRadius(12)
                            }
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Manage Campaign")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
        }
    }

    private var postUpdateSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("POST UPDATE")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)

            TextEditor(text: $viewModel.updateContent)
                .frame(height: 80)
                .padding(8)
                .background(Color(.systemGray6))
                .cornerRadius(12)

            if let updateErrorMessage = viewModel.updateErrorMessage {
                Text(updateErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                Task { await viewModel.postUpdate() }
            } label: {
                if viewModel.isPostingUpdate {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Submit update").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isPostingUpdate || viewModel.updateContent.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }

    private var confirmDeliveredSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("ASSISTANCE")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)

            if let confirmErrorMessage = viewModel.confirmErrorMessage {
                Text(confirmErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                showConfirmDeliveredDialog = true
            } label: {
                if viewModel.isConfirmingDelivered {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Confirm assistance delivered").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isConfirmingDelivered)
            .confirmationDialog(
                "Confirm assistance was delivered?",
                isPresented: $showConfirmDeliveredDialog,
                titleVisibility: .visible
            ) {
                Button("Confirm") {
                    Task { await viewModel.confirmDelivered() }
                }
                Button("Cancel", role: .cancel) {}
            }
        }
    }

    private var submitProofSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SUBMIT ASSISTANCE PROOF")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)

            DatePicker("Delivery date", selection: $viewModel.proofDeliveryDate, displayedComponents: .date)

            TextField("Amount delivered", text: $viewModel.proofAmountDelivered)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.decimalPad)

            TextField("Notes (optional)", text: $viewModel.proofNotes)
                .textFieldStyle(.roundedBorder)

            proofPicker

            if viewModel.proofMediaId != nil {
                Text("✓ Proof attached")
                    .font(.footnote)
                    .foregroundColor(.green)
            }

            if let proofErrorMessage = viewModel.proofErrorMessage {
                Text(proofErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                Task { _ = await viewModel.submitProof() }
            } label: {
                if viewModel.isSubmittingProof {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Submit proof").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isSubmittingProof)
        }
    }

    private var finalReviewSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("● Final review")
                .font(.subheadline)
                .fontWeight(.semibold)
            Text("A Moderator is reviewing the submitted assistance proof before this campaign can be marked successful.")
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private var successfulSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("✓ Successful")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.green)
            Text("Assistance delivery and final review are complete.")
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private var proofPicker: some View {
        PhotosPicker(selection: $proofPhotoItem, matching: .images) {
            Label("Attach receipt or photo", systemImage: "doc.badge.plus")
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.bordered)
        .onChange(of: proofPhotoItem) { _, newItem in
            Task {
                guard let newItem = newItem,
                      let data = try? await newItem.loadTransferable(type: Data.self) else { return }
                await viewModel.uploadProofMedia(data: data, filename: "proof.jpg", mimeType: "image/jpeg")
                proofPhotoItem = nil
            }
        }
    }
}
