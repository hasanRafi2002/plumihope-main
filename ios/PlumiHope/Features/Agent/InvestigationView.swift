import SwiftUI
import PhotosUI

struct InvestigationView: View {
    @StateObject private var viewModel: InvestigationViewModel
    @State private var photoItem: PhotosPickerItem?
    @State private var showDecisionConfirm = false
    @State private var pendingEligible = true
    @Environment(\.dismiss) private var dismiss

    init(requestId: UUID) {
        _viewModel = StateObject(wrappedValue: InvestigationViewModel(requestId: requestId))
    }

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.request == nil {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let request = viewModel.request {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        Text(request.category.capitalized.replacingOccurrences(of: "_", with: " "))
                            .font(.title2)
                            .fontWeight(.bold)

                        Text("● " + request.status.capitalized.replacingOccurrences(of: "_", with: " "))
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        Divider()

                        Text("CHECKLIST")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        checklist

                        Divider()

                        Text("FIELD NOTES")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        TextEditor(text: $viewModel.fieldNotes)
                            .frame(height: 100)
                            .padding(8)
                            .background(Color(.systemGray6))
                            .cornerRadius(12)

                        if let noteErrorMessage = viewModel.noteErrorMessage {
                            Text(noteErrorMessage)
                                .font(.footnote)
                                .foregroundColor(.red)
                        }

                        Button {
                            Task { await viewModel.saveNote() }
                        } label: {
                            if viewModel.isSavingNote {
                                ProgressView().frame(maxWidth: .infinity)
                            } else {
                                Text("Save note").frame(maxWidth: .infinity)
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.isSavingNote || viewModel.fieldNotes.trimmingCharacters(in: .whitespaces).isEmpty)

                        Divider()

                        Text("EVIDENCE")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)

                        evidencePickerButton
                        .onChange(of: photoItem) { _, newItem in
                            Task {
                                guard let newItem = newItem,
                                      let data = try? await newItem.loadTransferable(type: Data.self) else { return }
                                await viewModel.uploadEvidence(
                                    data: data, filename: "evidence.jpg", mimeType: "image/jpeg", evidenceType: "RECIPIENT_PHOTO"
                                )
                                photoItem = nil
                            }
                        }

                        if let uploadErrorMessage = viewModel.uploadErrorMessage {
                            Text(uploadErrorMessage)
                                .font(.footnote)
                                .foregroundColor(.red)
                        }

                        ForEach(viewModel.events.filter { $0.eventType == "EVIDENCE_UPLOADED" }) { event in
                            Text("✓ \(event.notes ?? "Evidence uploaded")")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                        }

                        Divider()

                        if let decisionErrorMessage = viewModel.decisionErrorMessage {
                            Text(decisionErrorMessage)
                                .font(.footnote)
                                .foregroundColor(.red)
                        }

                        if request.status == "INVESTIGATING" {
                            VStack(spacing: 12) {
                                Button {
                                    pendingEligible = false
                                    showDecisionConfirm = true
                                } label: {
                                    Text("Case not suitable").frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.bordered)
                                .tint(.red)
                                .disabled(viewModel.isSubmittingDecision)

                                Button {
                                    pendingEligible = true
                                    showDecisionConfirm = true
                                } label: {
                                    if viewModel.isSubmittingDecision {
                                        ProgressView().frame(maxWidth: .infinity)
                                    } else {
                                        Text("Confirm verified case").frame(maxWidth: .infinity)
                                    }
                                }
                                .buttonStyle(.borderedProminent)
                                .disabled(!viewModel.checklistComplete || viewModel.isSubmittingDecision)
                            }
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Investigation")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
            await viewModel.startInvestigationIfNeeded()
        }
        .confirmationDialog(
            pendingEligible ? "Confirm this case is verified?" : "Mark case as not suitable?",
            isPresented: $showDecisionConfirm,
            titleVisibility: .visible
        ) {
            Button(pendingEligible ? "Confirm" : "Not suitable", role: pendingEligible ? .none : .destructive) {
                Task {
                    let success = await viewModel.submitDecision(eligible: pendingEligible)
                    if success { dismiss() }
                }
            }
            Button("Cancel", role: .cancel) {}
        }
    }

    private var evidencePickerButton: some View {
        let uploading = viewModel.isUploading
        return PhotosPicker(selection: $photoItem, matching: .images) {
            if uploading {
                ProgressView().frame(maxWidth: .infinity)
            } else {
                Label("Add photo evidence", systemImage: "camera")
                    .frame(maxWidth: .infinity)
            }
        }
        .buttonStyle(.bordered)
        .disabled(uploading)
    }

    private var checklist: some View {
        VStack(alignment: .leading, spacing: 10) {
            checklistRow("Recipient information checked", $viewModel.checklistRecipientInfo)
            checklistRow("Location visit completed", $viewModel.checklistLocationVisit)
            checklistRow("Supporting documents collected", $viewModel.checklistDocuments)
            checklistRow("Need assessed", $viewModel.checklistNeedAssessed)
            HStack(spacing: 8) {
                Image(systemName: viewModel.checklistEvidenceUploaded ? "checkmark.square.fill" : "square")
                    .foregroundColor(viewModel.checklistEvidenceUploaded ? .green : .secondary)
                Text("Evidence uploaded")
                    .foregroundColor(.primary)
            }
        }
    }

    private func checklistRow(_ label: String, _ binding: Binding<Bool>) -> some View {
        Button {
            binding.wrappedValue.toggle()
        } label: {
            HStack(spacing: 8) {
                Image(systemName: binding.wrappedValue ? "checkmark.square.fill" : "square")
                    .foregroundColor(binding.wrappedValue ? .green : .secondary)
                Text(label)
                    .foregroundColor(.primary)
            }
        }
        .buttonStyle(.plain)
    }
}
