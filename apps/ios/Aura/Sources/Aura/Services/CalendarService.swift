// CalendarService.swift
// EventKit reader stub. See technical_spec.md §10.2.
// The CalendarAgent calls `eventsToday()` once per orchestrator tick and
// `nextEvent()` for the morning brief.
#if canImport(EventKit)
import EventKit
import Foundation

public actor CalendarService {
	private let store = EKEventStore()

	public init() {}

	public enum CalendarServiceError: Error {
		case notAuthorized
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

	public func eventsToday() throws -> [EKEvent] {
		let calendar = Calendar.current
		let start = calendar.startOfDay(for: Date())
		guard let end = calendar.date(byAdding: .day, value: 1, to: start) else { return [] }
		let predicate = store.predicateForEvents(withStart: start, end: end, calendars: nil)
		return store.events(matching: predicate).sorted { $0.startDate < $1.startDate }
	}

	public func nextEvent(from now: Date = Date()) throws -> EKEvent? {
		let calendar = Calendar.current
		guard let end = calendar.date(byAdding: .day, value: 2, to: now) else { return nil }
		let predicate = store.predicateForEvents(withStart: now, end: end, calendars: nil)
		return store.events(matching: predicate).sorted { $0.startDate < $1.startDate }.first
	}
}
#else
import Foundation

public actor CalendarService {
	public init() {}
	public func requestPermissions() async throws {}
	public func eventsToday() throws -> [Any] { [] }
	public func nextEvent(from now: Date = Date()) throws -> Any? { nil }
}
#endif
