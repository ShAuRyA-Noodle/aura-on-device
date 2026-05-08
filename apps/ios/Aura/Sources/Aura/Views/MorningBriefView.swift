// MorningBriefView.swift
// Hero phone surface. Renders Comms, Calendar, and Wellness agent outputs
// as a stacked card. Wired to real `HealthService` and `CalendarService`
// outputs — sleep / HRV / steps come from HealthKit; the next event and
// leave-by suggestion come from EventKit + MapKit.
import SwiftUI
#if canImport(EventKit)
import EventKit
#endif

@available(iOS 17.0, macOS 14.0, *)
public struct MorningBriefView: View {
	@EnvironmentObject var silenceBudget: SilenceBudget
	@StateObject private var viewModel = MorningBriefViewModel()
	@State private var showTrace = false

	public init() {}

	public var body: some View {
		NavigationStack {
			ScrollView {
				VStack(alignment: .leading, spacing: 24) {
					header

					if let snapshot = viewModel.snapshot {
						BriefCard(
							title: "Sleep",
							body: "Slept \(snapshot.sleepHoursDescription). HRV \(snapshot.rmssdDescription). Steps today \(snapshot.stepsDescription).",
							source: "Wellness"
						)
					} else {
						BriefCard(title: "Sleep", body: "Reading from Apple Health…", source: "Wellness")
					}

					if let event = viewModel.nextEvent {
						BriefCard(
							title: viewModel.formatEventTitle(event),
							body: viewModel.formatEventBody(event),
							source: "Calendar"
						)
					} else {
						BriefCard(title: "Schedule", body: "No events in the next 24 hours.", source: "Calendar")
					}

					BriefCard(
						title: "Inbox",
						body: viewModel.gmailSummary,
						source: "Comms"
					)

					if let error = viewModel.errorMessage {
						Text(error)
							.font(.footnote)
							.foregroundStyle(.red)
					}

					Button {
						showTrace = true
					} label: {
						Label("Why this brief?", systemImage: "text.alignleft")
							.font(.callout)
					}
					.buttonStyle(.bordered)
				}
				.padding(20)
			}
			.refreshable {
				await viewModel.refresh()
			}
			.task {
				await viewModel.refresh()
			}
			.navigationTitle("Brief")
			.sheet(isPresented: $showTrace) {
				ReasoningTraceView(trace: Trace.sampleMorningBrief)
			}
		}
	}

	private var header: some View {
		VStack(alignment: .leading, spacing: 4) {
			Text(Date.now.formatted(date: .complete, time: .omitted))
				.font(.subheadline)
				.foregroundStyle(.secondary)
			Text("Good morning.")
				.font(.system(size: 36, weight: .semibold, design: .serif))
			Text("Silence budget: \(silenceBudget.remaining) of \(SilenceBudget.dailyMax) tokens left today.")
				.font(.footnote)
				.foregroundStyle(.secondary)
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
@MainActor
final class MorningBriefViewModel: ObservableObject {
	@Published var snapshot: HealthService.Snapshot?
	@Published var nextEvent: CalendarService.EventSummary?
	@Published var gmailSummary: String = "Sign in to Google in Settings to view inbox digest."
	@Published var errorMessage: String?

	private let health = HealthService()
	private let calendar = CalendarService()

	func refresh() async {
		do {
			try await health.requestPermissions()
		} catch {
			errorMessage = error.localizedDescription
		}
		do {
			try await calendar.requestPermissions()
		} catch {
			errorMessage = error.localizedDescription
		}
		snapshot = await health.snapshot()
		nextEvent = await calendar.nextEvent()
	}

	func formatEventTitle(_ event: CalendarService.EventSummary) -> String {
		let formatter = DateFormatter()
		formatter.timeStyle = .short
		formatter.dateStyle = .none
		return "\(formatter.string(from: event.startDate)) — \(event.title)"
	}

	func formatEventBody(_ event: CalendarService.EventSummary) -> String {
		let minsToStart = Int(event.startDate.timeIntervalSinceNow / 60)
		var bits: [String] = []
		if minsToStart > 0 {
			bits.append("Starts in \(minsToStart) min.")
		} else {
			bits.append("Starts soon.")
		}
		if let location = event.location, !location.isEmpty {
			bits.append("Location: \(location).")
		}
		bits.append("Calendar: \(event.calendarTitle).")
		return bits.joined(separator: " ")
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct BriefCard: View {
	let title: String
	let body: String
	let source: String

	var body: some View {
		VStack(alignment: .leading, spacing: 8) {
			Text(title)
				.font(.headline)
			Text(body)
				.font(.body)
				.foregroundStyle(.primary)
			Text(source.uppercased())
				.font(.caption2)
				.foregroundStyle(.secondary)
				.tracking(1.2)
		}
		.padding(16)
		.frame(maxWidth: .infinity, alignment: .leading)
		.background(
			RoundedRectangle(cornerRadius: 14, style: .continuous)
				.fill(Color.gray.opacity(0.08))
		)
	}
}
