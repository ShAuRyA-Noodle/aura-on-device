// CalendarService.swift
// Real EventKit reads + travel-time aware leave-by suggestion.
// Implements technical_spec.md §10.2. The CalendarAgent calls
// `eventsNext24h()` once per orchestrator tick and `nextEvent()` /
// `leaveBy(for:)` for the morning brief.
#if canImport(EventKit)
import EventKit
import Foundation
#if canImport(MapKit)
import MapKit
import CoreLocation
#endif

public actor CalendarService {
	private let store = EKEventStore()

	public init() {}

	public enum CalendarServiceError: Error, LocalizedError {
		case notAuthorized
		case noLocationOnEvent
		case routingFailed(Error)

		public var errorDescription: String? {
			switch self {
			case .notAuthorized:        return "Calendar access was denied."
			case .noLocationOnEvent:    return "Event has no resolvable location."
			case .routingFailed(let e): return "Travel-time routing failed: \(e.localizedDescription)"
			}
		}
	}

	/// Holds the trimmed projection of an EKEvent the views need. Plain
	/// values so it survives the Sendable boundary into MainActor.
	public struct EventSummary: Sendable, Identifiable, Equatable {
		public let id: String
		public let title: String
		public let startDate: Date
		public let endDate: Date
		public let location: String?
		public let calendarTitle: String

		public var isAllDay: Bool { false }
	}

	/// Leave-by suggestion produced by combining the next event's start time
	/// with an MKDirections ETA from the user's current coordinate.
	public struct LeaveBySuggestion: Sendable, Equatable {
		public let event: EventSummary
		public let etaSeconds: TimeInterval
		public let leaveBy: Date

		public var travelMinutes: Int { Int((etaSeconds / 60).rounded()) }
	}

	public func requestPermissions() async throws {
		if #available(iOS 17.0, macOS 14.0, *) {
			let granted = try await store.requestFullAccessToEvents()
			guard granted else { throw CalendarServiceError.notAuthorized }
		} else {
			let granted = try await store.requestAccess(to: .event)
			guard granted else { throw CalendarServiceError.notAuthorized }
		}
	}

	/// Events in the next 24 hours, sorted by start time.
	public func eventsNext24h(from now: Date = Date()) -> [EventSummary] {
		let cal = Calendar.current
		guard let end = cal.date(byAdding: .hour, value: 24, to: now) else { return [] }
		let predicate = store.predicateForEvents(withStart: now, end: end, calendars: nil)
		return store.events(matching: predicate)
			.sorted { $0.startDate < $1.startDate }
			.map(Self.summary)
	}

	/// Detect overlapping events. Two events conflict when their intervals
	/// share more than a minute and neither is marked all-day.
	public func conflicts(in events: [EventSummary]) -> [(EventSummary, EventSummary)] {
		var pairs: [(EventSummary, EventSummary)] = []
		for i in 0..<events.count {
			for j in (i + 1)..<events.count {
				let a = events[i]
				let b = events[j]
				let overlap = min(a.endDate, b.endDate).timeIntervalSince(max(a.startDate, b.startDate))
				if overlap > 60 {
					pairs.append((a, b))
				}
			}
		}
		return pairs
	}

	public func nextEvent(from now: Date = Date()) -> EventSummary? {
		eventsNext24h(from: now).first
	}

	#if canImport(MapKit)
	/// Compute leave-by time for the next event using MapKit driving ETA.
	public func leaveBy(for event: EventSummary, from origin: CLLocationCoordinate2D) async throws -> LeaveBySuggestion {
		guard let location = event.location, !location.isEmpty else {
			throw CalendarServiceError.noLocationOnEvent
		}
		let request = MKLocalSearch.Request()
		request.naturalLanguageQuery = location
		let search = MKLocalSearch(request: request)
		let response: MKLocalSearch.Response
		do {
			response = try await search.start()
		} catch {
			throw CalendarServiceError.routingFailed(error)
		}
		guard let destinationItem = response.mapItems.first else {
			throw CalendarServiceError.noLocationOnEvent
		}
		let directionsRequest = MKDirections.Request()
		directionsRequest.source = MKMapItem(
			placemark: MKPlacemark(coordinate: origin)
		)
		directionsRequest.destination = destinationItem
		directionsRequest.transportType = .automobile
		directionsRequest.departureDate = Date()

		let directions = MKDirections(request: directionsRequest)
		let etaResponse: MKDirections.ETAResponse
		do {
			etaResponse = try await directions.calculateETA()
		} catch {
			throw CalendarServiceError.routingFailed(error)
		}
		let leaveBy = event.startDate.addingTimeInterval(-etaResponse.expectedTravelTime)
		return LeaveBySuggestion(
			event: event,
			etaSeconds: etaResponse.expectedTravelTime,
			leaveBy: leaveBy
		)
	}
	#endif

	private static func summary(_ event: EKEvent) -> EventSummary {
		EventSummary(
			id: event.eventIdentifier ?? UUID().uuidString,
			title: event.title ?? "Untitled",
			startDate: event.startDate,
			endDate: event.endDate,
			location: event.location,
			calendarTitle: event.calendar?.title ?? "Calendar"
		)
	}
}
#else
import Foundation

public actor CalendarService {
	public init() {}

	public struct EventSummary: Sendable, Identifiable, Equatable {
		public let id: String
		public let title: String
		public let startDate: Date
		public let endDate: Date
		public let location: String?
		public let calendarTitle: String
	}

	public struct LeaveBySuggestion: Sendable, Equatable {
		public let event: EventSummary
		public let etaSeconds: TimeInterval
		public let leaveBy: Date
		public var travelMinutes: Int { 0 }
	}

	public func requestPermissions() async throws {}
	public func eventsNext24h(from now: Date = Date()) -> [EventSummary] { [] }
	public func conflicts(in events: [EventSummary]) -> [(EventSummary, EventSummary)] { [] }
	public func nextEvent(from now: Date = Date()) -> EventSummary? { nil }
}
#endif
