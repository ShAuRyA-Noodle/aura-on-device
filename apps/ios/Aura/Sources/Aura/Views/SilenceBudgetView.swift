// SilenceBudgetView.swift
// Three-token meter, refund button, and the running list of today's spent
// surfaces. Persists via `SilenceBudget` (UserDefaults + iCloud KVS).
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct SilenceBudgetView: View {
	@EnvironmentObject var silenceBudget: SilenceBudget

	public init() {}

	public var body: some View {
		NavigationStack {
			List {
				Section("Today") {
					HStack(spacing: 12) {
						ForEach(0..<SilenceBudget.dailyMax, id: \.self) { idx in
							TokenDot(filled: idx < silenceBudget.remaining)
						}
						Spacer()
						Text("\(silenceBudget.remaining)/\(SilenceBudget.dailyMax)")
							.font(.system(.title3, design: .monospaced))
					}
					.padding(.vertical, 8)
				}

				Section("Spent today") {
					if silenceBudget.spentToday.isEmpty {
						Text("Nothing spent yet.")
							.foregroundStyle(.secondary)
					} else {
						ForEach(silenceBudget.spentToday) { entry in
							HStack {
								Text(entry.reason.isEmpty ? "Proactive surface" : entry.reason)
								Spacer()
								Text(entry.date.formatted(date: .omitted, time: .shortened))
									.font(.caption)
									.foregroundStyle(.secondary)
							}
						}
					}
				}

				Section("Actions") {
					Button {
						silenceBudget.refund(reason: "useful")
					} label: {
						Label("Refund a token (this nudge was useful)", systemImage: "arrow.uturn.left")
					}
					.disabled(silenceBudget.remaining >= SilenceBudget.dailyMax)

					Button(role: .destructive) {
						silenceBudget.resetForNewDay()
					} label: {
						Label("Reset to \(SilenceBudget.dailyMax) tokens", systemImage: "arrow.clockwise")
					}
				}
			}
			.navigationTitle("Silence budget")
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct TokenDot: View {
	let filled: Bool

	var body: some View {
		Circle()
			.stroke(Color.primary, lineWidth: 1.5)
			.background(
				Circle().fill(filled ? Color.primary : .clear)
			)
			.frame(width: 22, height: 22)
	}
}
