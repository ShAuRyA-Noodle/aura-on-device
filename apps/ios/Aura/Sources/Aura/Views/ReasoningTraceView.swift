// ReasoningTraceView.swift
// The visual signature of Aura. Renders a Reasoning Trace as inspectable
// JSON plus a structured breakdown. Sections in order per technical_spec.md
// §5.3: Why now → What I saw → What I considered → What I chose and why
// → What you can do.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct ReasoningTraceView: View {
	let trace: Trace
	@Environment(\.dismiss) private var dismiss

	public init(trace: Trace) {
		self.trace = trace
	}

	public var body: some View {
		NavigationStack {
			ScrollView {
				VStack(alignment: .leading, spacing: 20) {
					whyNow
					whatISaw
					whatIConsidered
					whatIChose
					whatYouCanDo
					Divider().padding(.vertical, 8)
					rawJSON
				}
				.padding(20)
			}
			.navigationTitle("Reasoning Trace")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Close") { dismiss() }
				}
			}
		}
	}

	private var whyNow: some View {
		section(label: "Why now") {
			Text("\(trace.trigger.source)")
				.font(.system(.body, design: .monospaced))
		}
	}

	private var whatISaw: some View {
		section(label: "What I saw") {
			VStack(alignment: .leading, spacing: 6) {
				ForEach(Array(trace.signals.enumerated()), id: \.offset) { _, sig in
					HStack(alignment: .firstTextBaseline) {
						Text(sig.k)
							.font(.system(.callout, design: .monospaced))
							.foregroundStyle(.secondary)
						Spacer()
						Text(sig.displayValue)
							.font(.system(.callout, design: .monospaced))
					}
				}
			}
		}
	}

	private var whatIConsidered: some View {
		section(label: "What I considered") {
			VStack(alignment: .leading, spacing: 8) {
				ForEach(trace.candidates, id: \.kind) { cand in
					HStack {
						Text(cand.kind)
							.font(.system(.callout, design: .monospaced))
						Spacer()
						Text(String(format: "%.2f", cand.score))
							.font(.system(.callout, design: .monospaced))
							.foregroundStyle(.secondary)
					}
				}
			}
		}
	}

	private var whatIChose: some View {
		section(label: "What I chose and why") {
			VStack(alignment: .leading, spacing: 6) {
				Text(trace.chosen)
					.font(.headline)
				Text(trace.rationale)
					.font(.body)
					.foregroundStyle(.secondary)
			}
		}
	}

	private var whatYouCanDo: some View {
		section(label: "What you can do") {
			HStack(spacing: 12) {
				Button("Confirm") {}
					.buttonStyle(.borderedProminent)
				Button("Dismiss") {}
					.buttonStyle(.bordered)
				Button("Edit") {}
					.buttonStyle(.bordered)
			}
		}
	}

	private var rawJSON: some View {
		section(label: "Raw trace") {
			Text(trace.prettyJSON ?? "{ }")
				.font(.system(.caption, design: .monospaced))
				.frame(maxWidth: .infinity, alignment: .leading)
				.padding(12)
				.background(
					RoundedRectangle(cornerRadius: 8)
						.fill(Color.gray.opacity(0.08))
				)
				.textSelection(.enabled)
		}
	}

	@ViewBuilder
	private func section<Content: View>(label: String, @ViewBuilder _ content: () -> Content) -> some View {
		VStack(alignment: .leading, spacing: 10) {
			Text(label.uppercased())
				.font(.caption)
				.foregroundStyle(.secondary)
				.tracking(1.4)
			content()
		}
	}
}
