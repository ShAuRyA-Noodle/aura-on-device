// PermissionFlow.swift
// Progressive permission ask, one rationale screen per capability.
// Implements the Phase 1 consent pattern from plan.md §1.3 — every step
// shows a plain-English rationale before the system prompt is invoked.
import SwiftUI
#if canImport(UserNotifications)
import UserNotifications
#endif

@available(iOS 17.0, macOS 14.0, *)
public struct PermissionFlow: View {
	public enum Step: Int, CaseIterable, Identifiable {
		case welcome
		case health
		case calendar
		case notifications
		case localNetwork
		case done

		public var id: Int { rawValue }
	}

	@State private var step: Step = .welcome
	@State private var statusMessage: String?
	@Environment(\.dismiss) private var dismiss

	public var onComplete: () -> Void

	public init(onComplete: @escaping () -> Void = {}) {
		self.onComplete = onComplete
	}

	public var body: some View {
		NavigationStack {
			VStack {
				switch step {
				case .welcome:
					rationale(
						title: "Aura runs on-device",
						body: "Aura uses your phone's Health, Calendar, Mail, and Notifications data to compose one calm card per day. Every reading stays on the device unless you explicitly export it.",
						buttonTitle: "Continue"
					) { step = .health }
				case .health:
					rationale(
						title: "Apple Health",
						body: "Aura reads HRV, sleep, heart rate, and step count to compute the Wellness Load Score. Aura does not write to Health and does not upload these readings.",
						buttonTitle: "Allow Health"
					) { Task { await requestHealth() } }
				case .calendar:
					rationale(
						title: "Calendar",
						body: "Aura reads upcoming events to surface conflicts and a leave-by alert. Calendar data is read only — Aura never edits or sends events.",
						buttonTitle: "Allow Calendar"
					) { Task { await requestCalendar() } }
				case .notifications:
					rationale(
						title: "Notifications",
						body: "Aura sends at most three proactive nudges per day, capped by the Silence Budget. You can lower the cap to zero in Settings.",
						buttonTitle: "Allow Notifications"
					) { Task { await requestNotifications() } }
				case .localNetwork:
					rationale(
						title: "Local Wi-Fi",
						body: "Aura uses your local Wi-Fi to hand off the current card between your iPhone, iPad, and Mac. Nothing is sent to the internet.",
						buttonTitle: "Allow Local Network"
					) { step = .done }
				case .done:
					VStack(spacing: 18) {
						Text("You're set.")
							.font(.system(size: 32, weight: .semibold, design: .serif))
						Text("You can revisit any of these in Settings → Permissions.")
							.font(.callout)
							.foregroundStyle(.secondary)
							.multilineTextAlignment(.center)
						Button("Open Aura") {
							onComplete()
							dismiss()
						}
						.buttonStyle(.borderedProminent)
					}
					.padding(32)
				}
				if let statusMessage {
					Text(statusMessage)
						.font(.footnote)
						.foregroundStyle(.secondary)
						.padding(.horizontal, 32)
				}
			}
			.navigationTitle("Welcome")
			.toolbar {
				ToolbarItem(placement: .cancellationAction) {
					Button("Skip") {
						onComplete()
						dismiss()
					}
				}
			}
		}
	}

	private func rationale(title: String, body: String, buttonTitle: String, action: @escaping () -> Void) -> some View {
		VStack(spacing: 18) {
			Text(title)
				.font(.system(size: 32, weight: .semibold, design: .serif))
				.frame(maxWidth: .infinity, alignment: .leading)
			Text(body)
				.font(.body)
				.foregroundStyle(.primary)
				.frame(maxWidth: .infinity, alignment: .leading)
			Spacer()
			Button(buttonTitle, action: action)
				.buttonStyle(.borderedProminent)
				.controlSize(.large)
		}
		.padding(28)
	}

	@MainActor
	private func requestHealth() async {
		do {
			try await HealthService().requestPermissions()
			statusMessage = nil
		} catch {
			statusMessage = error.localizedDescription
		}
		step = .calendar
	}

	@MainActor
	private func requestCalendar() async {
		do {
			try await CalendarService().requestPermissions()
			statusMessage = nil
		} catch {
			statusMessage = error.localizedDescription
		}
		step = .notifications
	}

	@MainActor
	private func requestNotifications() async {
		#if canImport(UserNotifications)
		do {
			_ = try await UNUserNotificationCenter.current()
				.requestAuthorization(options: [.alert, .badge, .sound])
			statusMessage = nil
		} catch {
			statusMessage = error.localizedDescription
		}
		#endif
		step = .localNetwork
	}
}
