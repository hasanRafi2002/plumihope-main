import SwiftUI
import PhotosUI

struct CreateCampaignView: View {
    @StateObject private var viewModel: CreateCampaignViewModel
    @State private var step: Int = 1
    @State private var photoItem: PhotosPickerItem?
    @Environment(\.dismiss) private var dismiss
    var onCompleted: () -> Void

    init(helpRequest: HelpRequestDetail, onCompleted: @escaping () -> Void) {
        _viewModel = StateObject(wrappedValue: CreateCampaignViewModel(helpRequest: helpRequest))
        self.onCompleted = onCompleted
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Create campaign — Step \(step) of 4")
                    .font(.caption)
                    .foregroundColor(.secondary)

                switch step {
                case 1: basicsStep
                case 2: evidenceStep
                case 3: payoutStep
                default: reviewStep
                }
            }
            .padding()
        }
        .navigationTitle("New Campaign")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadCategories()
        }
    }

    // MARK: Step 1 — Basics + Recipient

    private var basicsStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            field("Title", $viewModel.title)

            VStack(alignment: .leading, spacing: 8) {
                Text("Description").font(.subheadline).foregroundColor(.secondary)
                TextEditor(text: $viewModel.description)
                    .frame(height: 100)
                    .padding(8)
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Category").font(.subheadline).foregroundColor(.secondary)
                if viewModel.isLoadingCategories {
                    ProgressView()
                } else {
                    Picker("Category", selection: $viewModel.selectedCategoryId) {
                        ForEach(viewModel.categories) { category in
                            Text(category.name.capitalized).tag(Optional(category.id))
                        }
                    }
                    .pickerStyle(.menu)
                }
            }

            field("Target amount", $viewModel.targetAmount)
                .keyboardType(.decimalPad)

            field("Recipient name", $viewModel.recipientName)
            field("Recipient relationship", $viewModel.recipientRelationship)

            if let createErrorMessage = viewModel.createErrorMessage {
                Text(createErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                Task {
                    await viewModel.createDraft()
                    if viewModel.campaign != nil { step = 2 }
                }
            } label: {
                if viewModel.isCreating {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Continue").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(!viewModel.canCreate || viewModel.isCreating)
        }
    }

    // MARK: Step 2 — Evidence

    private var evidenceStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Upload supporting evidence").font(.headline)

            PhotosPicker(selection: $photoItem, matching: .images) {
                Label("Add photo evidence", systemImage: "camera")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(viewModel.isUploadingEvidence)
            .onChange(of: photoItem) { _, newItem in
                Task {
                    guard let newItem = newItem,
                          let data = try? await newItem.loadTransferable(type: Data.self) else { return }
                    await viewModel.uploadEvidence(data: data, filename: "evidence.jpg", mimeType: "image/jpeg", evidenceType: "COST_ESTIMATE")
                    photoItem = nil
                }
            }

            if viewModel.isUploadingEvidence {
                ProgressView()
            }

            if let evidenceErrorMessage = viewModel.evidenceErrorMessage {
                Text(evidenceErrorMessage).font(.footnote).foregroundColor(.red)
            }

            ForEach(viewModel.evidenceItems) { item in
                Text("✓ \(item.evidenceType.capitalized)")
                    .font(.footnote)
                    .foregroundColor(.secondary)
            }

            Text("At least one evidence item is required before submission.")
                .font(.caption)
                .foregroundColor(.secondary)

            Button {
                step = 3
            } label: {
                Text("Continue").frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.evidenceItems.isEmpty)
        }
    }

    // MARK: Step 3 — Payout

    private var payoutStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Payout information").font(.headline)
            Text("This information is not publicly displayed.")
                .font(.footnote)
                .foregroundColor(.secondary)

            field("Payout destination (e.g. bKash number)", $viewModel.payoutDestinationRef)

            if let payoutErrorMessage = viewModel.payoutErrorMessage {
                Text(payoutErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                Task {
                    await viewModel.savePayout()
                    if viewModel.payoutSaved { step = 4 }
                }
            } label: {
                if viewModel.isSavingPayout {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Continue").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isSavingPayout)
        }
    }

    // MARK: Step 4 — Review + Submit

    private var reviewStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Review").font(.headline)

            reviewRow("Title", viewModel.title)
            reviewRow("Description", viewModel.description)
            reviewRow("Target amount", viewModel.targetAmount)
            reviewRow("Recipient", viewModel.recipientName.isEmpty ? "—" : viewModel.recipientName)
            reviewRow("Evidence items", "\(viewModel.evidenceItems.count)")

            if let submitErrorMessage = viewModel.submitErrorMessage {
                Text(submitErrorMessage).font(.footnote).foregroundColor(.red)
            }

            Button {
                Task {
                    await viewModel.submit()
                    if viewModel.submitted {
                        onCompleted()
                        dismiss()
                    }
                }
            } label: {
                if viewModel.isSubmitting {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    Text("Submit for Moderator review").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isSubmitting)
        }
    }

    private func field(_ label: String, _ text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label).font(.subheadline).foregroundColor(.secondary)
            TextField(label, text: text).textFieldStyle(.roundedBorder)
        }
    }

    private func reviewRow(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.caption).foregroundColor(.secondary)
            Text(value).font(.body)
        }
    }
}
