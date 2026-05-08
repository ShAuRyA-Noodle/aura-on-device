// ReasoningTraceView.swift
// The visual signature of Aura. Renders a Reasoning Trace as inspectable
// JSON plus a structured breakdown. Sections in order per technical_spec.md
// §5.3: Why now → What I saw → What I considered → What I chose and why →
// What you can do.
//
// Live mode: when no `trace` is supplied, the view subscribes to the
// `AuraBridge` WebSocket stream and renders the most recent trace, with
// JSON syntax-highlighting picking out `chosen`, `rationale`, and
// `confirm_required` in the brand sunset orange #FF5B2E. See
// `aura/design/screens/02_reasoning_trace_drawer.md`.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct ReasoningTraceView: View {
	private let staticTrace: Trace?
	@StateObject private var bridge = AuraBridge.shared
	@Environment(\.dismiss) private var dismiss

	public init(trace: Trace? = nil) {
		self.staticTrace = trace
	}

	private var resolvedTrace: Trace? {
		staticTrace ?? bridge.liveTraces.first
	}

	public var body: some View {
		NavigationStack {
			ScrollView {
				VStack(alignment: .leading, spacing: 20) {
					if let trace = resolvedTrace {
						sections(for: trace)
						Divider().padding(.vertical, 8)
						highlightedJSON(for: trace)
					} else {
						emptyState
					}
				}
				.padding(20)
			}
			.navigationTitle("Reasoning Trace")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Close") { dismiss() }
				}
				ToolbarItem(placement: .primaryAction) {
					connectionPill
				}
			}
			.task {
				if staticTrace == nil {
					_ = await bridge.ping()
					bridge.startTraceStream()
				}
			}
			.onDisappear {
				if staticTrace == nil {
					bridge.stopTraceStream()
				}
			}
		}
	}

	@ViewBuilder
	private func sections(for trace: Trace) -> some View {
		whyNow(trace)
		whatISaw(trace)
		whatIConsidered(trace)
		whatIChose(trace)
		whatYouCanDo(trace)
	}

	private var emptyState: some View {
		VStack(spacing: 12) {
			Text("No live trace yet")
				.font(.headline)
			Text(bridge.isConnected
				 ? "Listening on \(bridge.baseURL.absoluteString) — waiting for the orchestrator to emit the first trace."
				 : "Bridge unreachable. Start the FastAPI orchestrator on your Mac and re-open this drawer.")
				.font(.callout)
				.foregroundStyle(.secondary)
				.multilineTextAlignment(.center)
				.frame(maxWidth: .infinity)
		}
		.padding(.vertical, 40)
	}

	private var connectionPill: some View {
		Text(bridge.isConnected ? "live" : "offline")
			.font(.caption2)
			.tracking(1.2)
			.padding(.horizontal, 8)
			.padding(.vertical, 4)
			.foregroundStyle(bridge.isConnected ? Color(red: 1.0, green: 0.357, blue: 0.18) : .secondary)
			.background(
				Capsule().stroke(
					bridge.isConnected ? Color(red: 1.0, green: 0.357, blue: 0.18) : Color.gray,
					lineWidth: 1
				)
			)
	}

	private func whyNow(_ trace: Trace) -> some View {
		section(label: "Why now") {
			Text(trace.trigger.source)
				.font(.system(.body, design: .monospaced))
		}
	}

	private func whatISaw(_ trace: Trace) -> some View {
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

	private func whatIConsidered(_ trace: Trace) -> some View {
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

	private func whatIChose(_ trace: Trace) -> some View {
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

	private func whatYouCanDo(_ trace: Trace) -> some View {
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

	private func highlightedJSON(for trace: Trace) -> some View {
		section(label: "Raw trace") {
			TraceJSONView(trace: trace)
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

/// Pretty-printed JSON view that highlights the three brand keys in
/// sunset orange #FF5B2E per the design spec.
@available(iOS 17.0, macOS 14.0, *)
struct TraceJSONView: View {
	let trace: Trace

	private static let highlightedKeys: Set<String> = [
		"chosen", "rationale", "confirm_required"
	]
	private static let accent = Color(red: 1.0, green: 0.357, blue: 0.18) // #FF5B2E

	var body: some View {
		Text(attributedJSON())
	}

	private func attributedJSON() -> AttributedString {
		guard let raw = trace.prettyJSON else {
			return AttributedString("{ }")
		}
		var attributed = AttributedString(raw)
		// For every highlighted key, scan the underlying String for occurrences,
		// translate each NSRange into AttributedString indices, and apply the
		// brand accent. This avoids mutating the AttributedString while
		// iterating, which is what previously caused index drift.
		let nsRaw = raw as NSString
		for key in Self.highlightedKeys {
			let needle = "\"\(key)\""
			var searchStart = 0
			while searchStart < nsRaw.length {
				let range = nsRaw.range(
					of: needle,
					options: [],
					range: NSRange(location: searchStart, length: nsRaw.length - searchStart)
				)
				if range.location == NSNotFound { break }
				if let lower = AttributedString.Index(
					String.Index(utf16Offset: range.location, in: raw),
					within: attributed
				), let upper = AttributedString.Index(
					String.Index(utf16Offset: range.location + range.length, in: raw),
					within: attributed
				) {
					let attrRange = lower..<upper
					attributed[attrRange].foregroundColor = Self.accent
					attributed[attrRange].font = .system(.caption, design: .monospaced).weight(.semibold)
				}
				searchStart = range.location + range.length
			}
		}
		return attributed
	}
}
