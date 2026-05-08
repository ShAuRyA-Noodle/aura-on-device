// AuraBridge.swift
// Networking layer that talks to the Mac-side FastAPI orchestrator over USB
// (or Bonjour-discovered Wi-Fi). REST for one-off fetches, WebSocket for
// the live Reasoning Trace stream.
//
// Default base URL is `http://localhost:8000`. When the iPhone is USB-tethered
// to the Mac with Personal Hotspot off, `localhost` resolves to the device
// itself; the bridge runs the orchestrator on the host and forwards HTTP via
// `usbmuxd`. Override with `Bridge.baseURL = URL(...)` for Wi-Fi mode.
import Foundation
#if canImport(Combine)
import Combine
#endif

@available(iOS 17.0, macOS 14.0, *)
@MainActor
public final class AuraBridge: ObservableObject {
	public static let shared = AuraBridge()

	public enum BridgeError: Error, LocalizedError {
		case notConnected
		case httpStatus(Int)
		case decodeFailed(Error)
		case socketClosed
		case socketReceive(Error)

		public var errorDescription: String? {
			switch self {
			case .notConnected:        return "Aura bridge is not reachable."
			case .httpStatus(let s):   return "Bridge returned HTTP \(s)."
			case .decodeFailed(let e): return "Bridge response decode failed: \(e.localizedDescription)"
			case .socketClosed:        return "Bridge WebSocket closed."
			case .socketReceive(let e): return "Bridge WebSocket receive failed: \(e.localizedDescription)"
			}
		}
	}

	@Published public private(set) var liveTraces: [Trace] = []
	@Published public private(set) var isConnected: Bool = false
	@Published public private(set) var lastError: String?

	public var baseURL: URL = URL(string: "http://localhost:8000") ?? URL(fileURLWithPath: "/")

	private var session: URLSession
	private var socket: URLSessionWebSocketTask?
	private var streamTask: Task<Void, Never>?

	public init(session: URLSession = .shared) {
		self.session = session
	}

	// MARK: - REST

	/// Health-check the bridge. Returns `true` when the bridge answers `200`.
	public func ping() async -> Bool {
		let url = baseURL.appendingPathComponent("/healthz")
		var request = URLRequest(url: url)
		request.timeoutInterval = 3
		do {
			let (_, response) = try await session.data(for: request)
			let ok = (response as? HTTPURLResponse)?.statusCode == 200
			isConnected = ok
			return ok
		} catch {
			isConnected = false
			lastError = error.localizedDescription
			return false
		}
	}

	/// Fetch the most recent traces from the bridge `/traces` endpoint.
	public func fetchRecentTraces(limit: Int = 25) async throws -> [Trace] {
		var components = URLComponents(
			url: baseURL.appendingPathComponent("/traces"),
			resolvingAgainstBaseURL: false
		)
		components?.queryItems = [URLQueryItem(name: "limit", value: String(limit))]
		guard let url = components?.url else { throw URLError(.badURL) }
		let (data, response) = try await session.data(from: url)
		guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
			throw BridgeError.httpStatus((response as? HTTPURLResponse)?.statusCode ?? -1)
		}
		do {
			return try JSONDecoder().decode([Trace].self, from: data)
		} catch {
			throw BridgeError.decodeFailed(error)
		}
	}

	// MARK: - WebSocket trace stream

	/// Open a WebSocket to `/ws/traces` and append every Trace into
	/// `liveTraces`. Idempotent — calling twice closes the prior stream.
	public func startTraceStream() {
		stopTraceStream()
		guard var components = URLComponents(
			url: baseURL.appendingPathComponent("/ws/traces"),
			resolvingAgainstBaseURL: false
		) else {
			lastError = "Bad bridge URL."
			return
		}
		components.scheme = (components.scheme == "https") ? "wss" : "ws"
		guard let socketURL = components.url else { return }
		let task = session.webSocketTask(with: socketURL)
		self.socket = task
		task.resume()
		isConnected = true

		streamTask = Task { [weak self] in
			await self?.receiveLoop(task: task)
		}
	}

	public func stopTraceStream() {
		streamTask?.cancel()
		streamTask = nil
		socket?.cancel(with: .goingAway, reason: nil)
		socket = nil
		isConnected = false
	}

	private func receiveLoop(task: URLSessionWebSocketTask) async {
		while !Task.isCancelled {
			do {
				let message = try await task.receive()
				let trace: Trace?
				switch message {
				case .data(let data):
					trace = try? JSONDecoder().decode(Trace.self, from: data)
				case .string(let text):
					if let data = text.data(using: .utf8) {
						trace = try? JSONDecoder().decode(Trace.self, from: data)
					} else {
						trace = nil
					}
				@unknown default:
					trace = nil
				}
				if let trace {
					self.liveTraces.insert(trace, at: 0)
					if self.liveTraces.count > 100 {
						self.liveTraces.removeLast(self.liveTraces.count - 100)
					}
				}
			} catch {
				self.isConnected = false
				self.lastError = error.localizedDescription
				break
			}
		}
	}
}
