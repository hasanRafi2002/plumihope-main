import Foundation
import Combine
import PhotosUI
import SwiftUI

@MainActor
final class InvestigationViewModel: ObservableObject {
    @Published var request: HelpRequestDetail?
    @Published var events: [HelpRequestEvent] = []
    @Published var isLoading = true
    @Published var errorMessage: String?

    @Published var fieldNotes: String = ""
    @Published var isSavingNote = false
    @Published var noteErrorMessage: String?

    @Published var isUploading = false
    @Published var uploadErrorMessage: String?

    @Published var checklistRecipientInfo = false
    @Published var checklistLocationVisit = false
    @Published var checklistDocuments = false
    @Published var checklistNeedAssessed = false
    @Published var checklistEvidenceUploaded = false

    @Published var isSubmittingDecision = false
    @Published var decisionErrorMessage: String?

    private let service = HelpRequestService.shared
    private let mediaService = MediaService.shared

    let requestId: UUID

    init(requestId: UUID) {
        self.requestId = requestId
    }

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let requestFetch = service.getHelpRequest(id: requestId)
            async let eventsFetch = service.listEvents(id: requestId)
            request = try await requestFetch
            events = try await eventsFetch
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func startInvestigationIfNeeded() async {
        guard let request = request, request.status == "CLAIMED" else { return }
        do {
            self.request = try await service.startInvestigation(id: requestId)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func saveNote() async {
        guard !fieldNotes.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isSavingNote = true
        noteErrorMessage = nil
        defer { isSavingNote = false }

        do {
            _ = try await service.addInvestigationNote(id: requestId, notes: fieldNotes)
            fieldNotes = ""
            events = try await service.listEvents(id: requestId)
        } catch {
            noteErrorMessage = error.localizedDescription
        }
    }

    func uploadEvidence(data: Data, filename: String, mimeType: String, evidenceType: String) async {
        isUploading = true
        uploadErrorMessage = nil
        defer { isUploading = false }

        do {
            let media = try await mediaService.uploadMedia(fileData: data, filename: filename, mimeType: mimeType)
            _ = try await service.logEvidenceUploaded(id: requestId, mediaId: media.id, evidenceType: evidenceType)
            checklistEvidenceUploaded = true
            events = try await service.listEvents(id: requestId)
        } catch {
            uploadErrorMessage = error.localizedDescription
        }
    }

    func submitDecision(eligible: Bool) async -> Bool {
        isSubmittingDecision = true
        decisionErrorMessage = nil
        defer { isSubmittingDecision = false }

        do {
            request = try await service.submitEligibilityDecision(id: requestId, eligible: eligible, notes: nil)
            return true
        } catch {
            decisionErrorMessage = error.localizedDescription
            return false
        }
    }

    var checklistComplete: Bool {
        checklistRecipientInfo && checklistLocationVisit && checklistDocuments
            && checklistNeedAssessed && checklistEvidenceUploaded
    }
}
