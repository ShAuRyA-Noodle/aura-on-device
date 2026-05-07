// MemoryView.swift
// Memory tab. User-facing controls for the on-device memory graph:
// export to JSON, delete by time-range, view audit log. All actions stubbed
// today; wired in Phase 2 against the SQLite + sqlite-vss store described
// in technical_spec.md §6.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct MemoryView: View {
	@State private var showExportConfirm = false
	@State private var showDeleteSheet = false
	@State private var showAuditLog = false

	public init() {}

	public var body: some View {
		NavigationStack {
			List {
				Section {
					LabeledContent("Nodes", value: "—")
					LabeledContent("Edges", value: "—")
					LabeledContent("Last write", value: "—")
				} header: {
					Text("Graph")
				} footer: {
					Text("Storage: SQLite with sqlite-vss, encrypted at rest with a key from the iOS Secure Enclave.")
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
			}
			.navigationTitle("Memory")
			.confirmationDialog(
				"Export your memory graph?",
				isPresented: $showExportConfirm,
				titleVisibility: .visible
			) {
				Button("Export") { /* stub */ }
				Button("Cancel", role: .cancel) {}
			} message: {
				Text("A JSON file will be written to the share sheet. Nothing leaves the device until you choose where to send it.")
			}
			.sheet(isPresented: $showDeleteSheet) {
				DeleteByRangeView()
			}
			.sheet(isPresented: $showAuditLog) {
				AuditLogView()
			}
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct DeleteByRangeView: View {
	@Environment(\.dismiss) private var dismiss
	@State private var start: Date = Calendar.current.date(byAdding: .day, value: -7, to: .now) ?? .now
	@State private var end: Date = .now

	var body: some View {
		NavigationStack {
			Form {
				DatePicker("From", selection: $start)
				DatePicker("To", selection: $end)

				Section {
					Button("Delete nodes in range", role: .destructive) {
						dismiss()
					}
				}
			}
			.navigationTitle("Delete by range")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Cancel") { dismiss() }
				}
			}
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct AuditLogView: View {
	@Environment(\.dismiss) private var dismiss

	var body: some View {
		NavigationStack {
			List {
				Section {
					Text("No audit entries yet.")
						.foregroundStyle(.secondary)
				} footer: {
					Text("Daily Merkle root: pending first write.")
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
}
