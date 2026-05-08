// GmailService.swift
// Real Gmail OAuth via GoogleSignIn-iOS, plus receipt-bearing thread fetch
// against the Gmail REST API.
// Implements technical_spec.md §10.3. Scopes: gmail.metadata + gmail.readonly.
//
// Receipts query string is fixed to Indian merchants the FinanceAgent and
// CommsAgent care about: Swiggy, Zomato, Blinkit, Amazon India, IRCTC.
#if canImport(UIKit) && canImport(GoogleSignIn)
import Foundation
import GoogleSignIn
import UIKit

public actor GmailService {
	public static let shared = GmailService()

	private init() {}

	public enum GmailServiceError: Error, LocalizedError {
		case noPresentingViewController
		case notSignedIn
		case httpStatus(Int)
		case decodeFailed
		case tokenRefreshFailed(Error)

		public var errorDescription: String? {
			switch self {
			case .noPresentingViewController: return "No view controller available to present sign-in sheet."
			case .notSignedIn:                return "Not signed in to Google."
			case .httpStatus(let s):          return "Gmail API returned status \(s)."
			case .decodeFailed:               return "Failed to decode Gmail API response."
			case .tokenRefreshFailed(let e):  return "Failed to refresh OAuth token: \(e.localizedDescription)"
			}
		}
	}

	public static let scopes = [
		"https://www.googleapis.com/auth/gmail.metadata",
		"https://www.googleapis.com/auth/gmail.readonly"
	]

	/// Receipt sender domains we care about. New merchants belong here.
	public static let receiptSenders: [String] = [
		"noreply@zomato.com",
		"noreply@swiggy.in",
		"no-reply@blinkit.com",
		"auto-confirm@amazon.in",
		"shipment-tracking@amazon.in",
		"order-update@amazon.in",
		"ticketadmin@irctc.co.in"
	]

	/// Compiled regexes for amount extraction. First match wins.
	private static let amountPatterns: [NSRegularExpression] = {
		let raw = [
			#"(?i)(?:Rs\.?|INR|₹)\s?([0-9]+(?:\.[0-9]{1,2})?)"#,
			#"(?i)total[^0-9]{1,12}([0-9]+(?:\.[0-9]{1,2})?)"#,
			#"(?i)amount[^0-9]{1,12}([0-9]+(?:\.[0-9]{1,2})?)"#
		]
		return raw.compactMap { try? NSRegularExpression(pattern: $0) }
	}()

	@MainActor
	public func signIn(presenting root: UIViewController) async throws -> GIDGoogleUser {
		let result = try await GIDSignIn.sharedInstance.signIn(
			withPresenting: root,
			hint: nil,
			additionalScopes: GmailService.scopes
		)
		return result.user
	}

	@MainActor
	public func restoreSession() async -> GIDGoogleUser? {
		await withCheckedContinuation { cont in
			GIDSignIn.sharedInstance.restorePreviousSignIn { user, _ in
				cont.resume(returning: user)
			}
		}
	}

	public func signOut() async {
		await MainActor.run {
			GIDSignIn.sharedInstance.signOut()
		}
	}

	/// Refresh the bearer token if needed, then return the current value.
	@MainActor
	private func freshAccessToken(for user: GIDGoogleUser) async throws -> String {
		try await withCheckedThrowingContinuation { cont in
			user.refreshTokensIfNeeded { refreshed, error in
				if let error {
					cont.resume(throwing: GmailServiceError.tokenRefreshFailed(error))
					return
				}
				cont.resume(returning: (refreshed ?? user).accessToken.tokenString)
			}
		}
	}

	/// Fetch up to `limit` recent receipt-bearing thread refs.
	public func recentReceipts(user: GIDGoogleUser, limit: Int = 50) async throws -> [ReceiptThread] {
		let token = try await freshAccessToken(for: user)
		let from = GmailService.receiptSenders.map { "from:\($0)" }.joined(separator: " OR ")
		let q = "newer_than:7d (\(from))"
		var components = URLComponents(string: "https://gmail.googleapis.com/gmail/v1/users/me/messages")
		components?.queryItems = [
			URLQueryItem(name: "q", value: q),
			URLQueryItem(name: "maxResults", value: String(limit))
		]
		guard let url = components?.url else { throw URLError(.badURL) }
		var request = URLRequest(url: url)
		request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
		let (data, response) = try await URLSession.shared.data(for: request)
		guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
			throw GmailServiceError.httpStatus((response as? HTTPURLResponse)?.statusCode ?? -1)
		}
		do {
			let decoded = try JSONDecoder().decode(ReceiptListResponse.self, from: data)
			return (decoded.messages ?? []).map { ReceiptThread(id: $0.id, threadId: $0.threadId) }
		} catch {
			throw GmailServiceError.decodeFailed
		}
	}

	/// Fetch metadata (subject, from, snippet) for a single message.
	public func metadata(for messageId: String, user: GIDGoogleUser) async throws -> ReceiptMetadata {
		let token = try await freshAccessToken(for: user)
		var components = URLComponents(
			string: "https://gmail.googleapis.com/gmail/v1/users/me/messages/\(messageId)"
		)
		components?.queryItems = [
			URLQueryItem(name: "format", value: "metadata"),
			URLQueryItem(name: "metadataHeaders", value: "Subject"),
			URLQueryItem(name: "metadataHeaders", value: "From"),
			URLQueryItem(name: "metadataHeaders", value: "Date")
		]
		guard let url = components?.url else { throw URLError(.badURL) }
		var request = URLRequest(url: url)
		request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
		let (data, response) = try await URLSession.shared.data(for: request)
		guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
			throw GmailServiceError.httpStatus((response as? HTTPURLResponse)?.statusCode ?? -1)
		}
		let envelope: MessageEnvelope
		do {
			envelope = try JSONDecoder().decode(MessageEnvelope.self, from: data)
		} catch {
			throw GmailServiceError.decodeFailed
		}
		let headers = envelope.payload?.headers ?? []
		let subject = headers.first(where: { $0.name.lowercased() == "subject" })?.value ?? ""
		let from = headers.first(where: { $0.name.lowercased() == "from" })?.value ?? ""
		let snippet = envelope.snippet ?? ""
		let amount = Self.parseAmount(in: subject) ?? Self.parseAmount(in: snippet)
		let merchant = Self.merchant(from: from)
		return ReceiptMetadata(
			id: messageId,
			subject: subject,
			from: from,
			snippet: snippet,
			merchant: merchant,
			amountRupees: amount
		)
	}

	/// Extract an amount in rupees from the supplied text.
	public static func parseAmount(in text: String) -> Double? {
		let range = NSRange(text.startIndex..., in: text)
		for regex in amountPatterns {
			guard let match = regex.firstMatch(in: text, range: range),
				  match.numberOfRanges >= 2,
				  let amountRange = Range(match.range(at: 1), in: text)
			else { continue }
			let raw = String(text[amountRange]).replacingOccurrences(of: ",", with: "")
			if let value = Double(raw) {
				return value
			}
		}
		return nil
	}

	/// Heuristic merchant tag from the From header.
	public static func merchant(from header: String) -> String {
		let lower = header.lowercased()
		if lower.contains("zomato")  { return "Zomato" }
		if lower.contains("swiggy")  { return "Swiggy" }
		if lower.contains("blinkit") { return "Blinkit" }
		if lower.contains("amazon")  { return "Amazon" }
		if lower.contains("irctc")   { return "IRCTC" }
		return "Other"
	}
}

public struct ReceiptListResponse: Codable {
	public let messages: [ReceiptMessageRef]?

	public struct ReceiptMessageRef: Codable {
		public let id: String
		public let threadId: String
	}
}

public struct ReceiptThread: Codable, Identifiable, Equatable, Sendable {
	public let id: String
	public let threadId: String
}

public struct ReceiptMetadata: Codable, Identifiable, Equatable, Sendable {
	public let id: String
	public let subject: String
	public let from: String
	public let snippet: String
	public let merchant: String
	public let amountRupees: Double?
}

private struct MessageEnvelope: Codable {
	let snippet: String?
	let payload: Payload?

	struct Payload: Codable {
		let headers: [Header]?
	}
	struct Header: Codable {
		let name: String
		let value: String
	}
}
#else
import Foundation

public actor GmailService {
	public static let shared = GmailService()
	private init() {}
	public static let scopes: [String] = []
	public static let receiptSenders: [String] = []
	public static func parseAmount(in text: String) -> Double? { nil }
	public static func merchant(from header: String) -> String { "Other" }
}

public struct ReceiptThread: Codable, Identifiable, Equatable, Sendable {
	public let id: String
	public let threadId: String
}

public struct ReceiptMetadata: Codable, Identifiable, Equatable, Sendable {
	public let id: String
	public let subject: String
	public let from: String
	public let snippet: String
	public let merchant: String
	public let amountRupees: Double?
}
#endif
