// MorningBriefView.swift
// Hero phone surface. Renders Comms, Calendar, and Wellness agent outputs as
// a stacked card. All data is stub today; agents will populate via the
// orchestrator in Phase 2.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct MorningBriefView: View {
	@EnvironmentObject var silenceBudget: SilenceBudget
	@State private var showTrace = false

	public init() {}

	public var body: some View {
		NavigationStack {
			ScrollView {
				VStack(alignment: .leading, spacing: 24) {
					header

					BriefCard(
						title: "Sleep",
						body: "Slept 5 hours 12 minutes. Push gym to evening.",
						source: "Wellness"
					)

					BriefCard(
						title: "9:00 — DSA Quiz",
						body: "Cab ETA 22 min. Leave by 8:15. Lecturer's slides summarised at 11:11pm last night.",
						source: "Calendar + Comms"
					)

					BriefCard(
						title: "Inbox",
						body: "12 unread, 1 from prof. 44 social messages batched.",
						source: "Comms"
					)

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
