// GmailService.swift
// Gmail OAuth + receipt fetch stub via GoogleSignIn-iOS. See
// technical_spec.md §10.3. Scopes: gmail.metadata + gmail.readonly.
//
// Receipts query string is fixed to Indian merchants the FinanceAgent and
// CommsAgent care about: Swiggy, Zomato, Blinkit, Amazon India, IRCTC.
#if canImport(UIKit) && canImport(GoogleSignIn)
import Foundation
import GoogleSignIn
import UIKit

public enum GmailService {
	public enum GmailServiceError: Error {
		case noPresentingViewController
		case httpStatus(Int)
		case decodeFailed
	}

	public static let scopes = [
		"https://www.googleapis.com/auth/gmail.metadata",
		"https://www.googleapis.com/auth/gmail.readonly"
	]

	@MainActor
	public static func signIn(presenting root: UIViewController) async throws -> GIDGoogleUser {
		let result = try await GIDSignIn.sharedInstance.signIn(
			withPresenting: root,
			hint: nil,
			additionalScopes: scopes
		)
		return result.user
	}

	public static func recentReceipts(user: GIDGoogleUser) async throws -> [ReceiptThread] {
		let token = user.accessToken.tokenString
		let q = "newer_than:7d (from:swiggy.in OR from:zomato.com OR from:blinkit.com OR from:amazon.in OR from:irctc.co.in)"
		var components = URLComponents(string: "https://gmail.googleapis.com/gmail/v1/users/me/messages")!
		components.queryItems = [
			URLQueryItem(name: "q", value: q),
			URLQueryItem(name: "maxResults", value: "50")
		]
		guard let url = components.url else { throw URLError(.badURL) }
		var request = URLRequest(url: url)
		request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
		let (data, response) = try await URLSession.shared.data(for: request)
		guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
			throw GmailServiceError.httpStatus((response as? HTTPURLResponse)?.statusCode ?? -1)
		}
		do {
			let decoded = try JSONDecoder().decode(ReceiptListResponse.self, from: data)
			return decoded.messages.map { ReceiptThread(id: $0.id, threadId: $0.threadId) }
		} catch {
			throw GmailServiceError.decodeFailed
		}
	}
}

public struct ReceiptListResponse: Codable {
	public let messages: [ReceiptMessageRef]

	public struct ReceiptMessageRef: Codable {
		public let id: String
		public let threadId: String
	}
}

public struct ReceiptThread: Codable, Identifiable, Equatable {
	public let id: String
	public let threadId: String
}
#else
import Foundation

public enum GmailService {
	public static let scopes: [String] = []
}

public struct ReceiptThread: Codable, Identifiable, Equatable {
	public let id: String
	public let threadId: String
}
#endif
