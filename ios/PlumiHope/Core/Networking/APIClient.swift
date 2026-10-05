import Foundation

final class APIClient {
    static let shared = APIClient()

    private let baseURL = "http://localhost:8000/api/v1"
    private let tokenStore: TokenStore = KeychainTokenStore()
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()

    private var isRefreshing = false

    private init() {}

    func request<T: Decodable>(
        _ endpoint: APIEndpoint,
        body: Encodable? = nil
    ) async throws -> T {
        let data = try await requestData(endpoint, body: body)
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }

    func requestNoContent(_ endpoint: APIEndpoint, body: Encodable? = nil) async throws {
        _ = try await requestData(endpoint, body: body)
    }

    func requestRawData(_ endpoint: APIEndpoint) async throws -> Data {
        return try await requestData(endpoint, body: nil)
    }

    private func requestData(_ endpoint: APIEndpoint, body: Encodable?, isRetry: Bool = false) async throws -> Data {
        guard var components = URLComponents(string: baseURL + endpoint.path) else {
            throw APIError.invalidURL
        }
        components.queryItems = endpoint.queryItems

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if endpoint.requiresAuth, let token = tokenStore.getAccessToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = try encoder.encode(body)
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown(URLError(.badServerResponse))
        }

        switch httpResponse.statusCode {
        case 200...299:
            return data
        case 401:
            if endpoint.requiresAuth && !isRetry {
                let refreshed = await attemptTokenRefresh()
                if refreshed {
                    return try await requestData(endpoint, body: body, isRetry: true)
                }
            }
            await MainActor.run {
                AuthManager.shared.logout()
            }
            throw APIError.unauthorized
        case 403:
            throw APIError.forbidden
        case 404:
            throw APIError.notFound
        default:
            let message = (try? decoder.decode([String: String].self, from: data))?["detail"] ?? "Server error"
            throw APIError.serverError(statusCode: httpResponse.statusCode, message: message)
        }
    }

    private func attemptTokenRefresh() async -> Bool {
        guard !isRefreshing else { return false }
        guard let refreshToken = tokenStore.getRefreshToken() else { return false }

        isRefreshing = true
        defer { isRefreshing = false }

        do {
            let tokens: TokenResponse = try await AuthService.shared.refresh(refreshToken: refreshToken)
            tokenStore.saveTokens(accessToken: tokens.accessToken, refreshToken: tokens.refreshToken)
            return true
        } catch {
            return false
        }
    }
}
