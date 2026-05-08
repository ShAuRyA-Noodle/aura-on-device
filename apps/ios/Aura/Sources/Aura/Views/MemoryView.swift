// MemoryView.swift
// Memory tab. User-facing controls for the on-device memory graph:
// export to JSON, delete by time-range, view audit log. Wired to the real
// `MemoryService` (GRDB-backed SQLite). Implements technical_spec.md §6.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct MemoryView: View {
	@StateObject private var viewModel = MemoryViewModel()
	@State private var showExportConfirm = false
	@State private var showDeleteSheet = false
	@State private var showAuditLog = false
	@State private var shareURL: URL?

	public init() {}

	public var body: some View {
		NavigationStack {
			List {
				Section {
					LabeledContent("Nodes", value: viewModel.nodeCountText)
					LabeledContent("Edges", value: viewModel.edgeCountText)
					LabeledContent("Last write", value: viewModel.lastWriteText)
				} header: {
					Text("Graph")
				} footer: {
					Text("Storage: SQLite via GRDB, file-protected at rest with iOS Data Protection (.completeFileProtection).")
				}

				Section("Controls") {
					Button {
						showExportConfirm = true
					} label: {
						Label("Export to JSON", systemImage: "square.and.arrow.up")
					}

					Button(role: .destructive) {
						showDeleteSheet = true
					} label: {
						Label("Delete by time range", systemImage: "trash")
					}

					Button {
						showAuditLog = true
					} label: {
						Label("View audit log", systemImage: "list.bullet.rectangle")
					}
				}

				Section("Retention") {
					LabeledContent("Raw messages", value: "0 days")
					LabeledContent("Structured events", value: "90 days")
					LabeledContent("Health snapshots", value: "365 days")
					LabeledContent("Reasoning traces", value: "30 days")
				}

				if let error = viewModel.errorMessage {
					Section("Status") {
						Text(error)
							.font(.footnote)
							.foregroundStyle(.red)
					}
				}
			}
			.task { await viewModel.refresh() }
			.refreshable { await viewModel.refresh() }
			.navigationTitle("Memory")
			.confirmationDialog(
				"Export your memory graph?",
				isPresented: $showExportConfirm,
				titleVisibility: .visible
			) {
				Button("Export") {
					Task {
						if let url = await viewModel.exportJSON() {
							shareURL = url
						}
					}
				}
				Button("Cancel", role: .cancel) {}
			} message: {
				Text("A JSON file will be written to your Files app. Nothing leaves the device until you choose where to send it.")
			}
			.sheet(isPresented: $showDeleteSheet) {
				DeleteByRangeView(viewModel: viewModel)
			}
			.sheet(isPresented: $showAuditLog) {
				AuditLogView(viewModel: viewModel)
			}
			#if canImport(UIKit)
			.sheet(item: Binding(
				get: { shareURL.map(IdentifiableURL.init) },
				set: { shareURL = $0?.url }
			)) { wrapped in
				ShareSheet(items: [wrapped.url])
			}
			#endif
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
@MainActor
final class MemoryViewModel: ObservableObject {
	@Published var nodeCountText = "—"
	@Published var edgeCountText = "—"
	@Published var lastWriteText = "—"
	@Published var auditEntries: [MemoryService.AuditEntry] = []
	@Published var errorMessage: String?

	private let service = MemoryService.shared

	func refresh() async {
		do {
			try await service.open()
			let nodes = try await service.nodeCount()
			let edges = try await service.edgeCount()
			let last = try await service.lastWrite()
			let entries = try await service.auditEntries(limit: 100)
			nodeCountText = String(nodes)
			edgeCountText = String(edges)
			if let last {
				let formatter = DateFormatter()
				formatter.dateStyle = .medium
				formatter.timeStyle = .short
				lastWriteText = formatter.string(from: last)
			} else {
				lastWriteText = "never"
			}
			auditEntries = entries
			errorMessage = nil
		} catch {
			errorMessage = error.localizedDescription
		}
	}

	func exportJSON() async -> URL? {
		do {
			return try await service.exportJSON()
		} catch {
			errorMessage = error.localizedDescription
			return nil
		}
	}

	func delete(start: Date, end: Date) async -> Int {
		do {
			let removed = try await service.deleteRange(start: start, end: end)
			await refresh()
			return removed
		} catch {
			errorMessage = error.localizedDescription
			return 0
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct DeleteByRangeView: View {
	@Environment(\.dismiss) private var dismiss
	@ObservedObject var viewModel: MemoryViewModel
	@State private var start: Date = Calendar.current.date(byAdding: .day, value: -7, to: .now) ?? .now
	@State private var end: Date = .now
	@State private var confirming = false

	var body: some View {
		NavigationStack {
			Form {
				DatePicker("From", selection: $start)
				DatePicker("To", selection: $end)

				Section {
					Button("Delete nodes in range", role: .destructive) {
						confirming = true
					}
				} footer: {
					Text("This is irreversible. The audit log keeps a record of the deletion.")
				}
			}
			.navigationTitle("Delete by range")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Cancel") { dismiss() }
				}
			}
			.confirmationDialog("Delete nodes in this range?", isPresented: $confirming) {
				Button("Delete", role: .destructive) {
					Task {
						_ = await viewModel.delete(start: start, end: end)
						dismiss()
					}
				}
				Button("Cancel", role: .cancel) {}
			} message: {
				Text("Deletes every node and trace timestamped between the selected dates.")
			}
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct AuditLogView: View {
	@Environment(\.dismiss) private var dismiss
	@ObservedObject var viewModel: MemoryViewModel

	var body: some View {
		NavigationStack {
			List {
				if viewModel.auditEntries.isEmpty {
					Section {
						Text("No audit entries yet.")
							.foregroundStyle(.secondary)
					} footer: {
						Text("The audit log is append-only and chained with SHA-256 — every entry references the hash of the previous row.")
					}
				} else {
					Section {
						ForEach(viewModel.auditEntries) { entry in
							VStack(alignment: .leading, spacing: 4) {
								HStack {
									Text(entry.op.uppercased())
										.font(.caption)
										.tracking(1.0)
										.foregroundStyle(.secondary)
									Spacer()
									Text(formatted(entry.ts))
										.font(.caption2)
										.foregroundStyle(.secondary)
								}
								if let target = entry.targetType {
									Text("\(target) \(entry.targetId ?? "")")
										.font(.callout)
								}
								Text(entry.hashChain.prefix(16) + "…")
									.font(.system(.caption2, design: .monospaced))
									.foregroundStyle(.secondary)
							}
							.padding(.vertical, 4)
						}
					}
				}
			}
			.navigationTitle("Audit log")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Close") { dismiss() }
				}
			}
		}
	}

	private func formatted(_ epoch: Int64) -> String {
		let date = Date(timeIntervalSince1970: TimeInterval(epoch))
		let formatter = DateFormatter()
		formatter.dateStyle = .short
		formatter.timeStyle = .short
		return formatter.string(from: date)
	}
}

private struct IdentifiableURL: Identifiable {
	let url: URL
	var id: URL { url }
}

#if canImport(UIKit)
import UIKit

private struct ShareSheet: UIViewControllerRepresentable {
	let items: [Any]

	func makeUIViewController(context: Context) -> UIActivityViewController {
		UIActivityViewController(activityItems: items, applicationActivities: nil)
	}

	func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
#endif
