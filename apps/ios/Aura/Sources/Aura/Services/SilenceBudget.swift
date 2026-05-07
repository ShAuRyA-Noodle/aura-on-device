// SilenceBudget.swift
// Implements the Silence Budget state from plan.md §1.2.
// Default daily quota: 3 tokens. Decrement on every proactive surface.
// Refund when the user taps "useful" on the surfaced card. Tracked as a
// Phase 2 KPI; visible in Settings and on the morning brief header.
import Foundation
#if canImport(Combine)
import Combine
#endif

@available(iOS 17.0, macOS 14.0, *)
public final class SilenceBudget: ObservableObject {
	public static let dailyMax: Int = 3

	@Published public private(set) var remaining: Int
	@Published public private(set) var lastResetDay: Date

	private let calendar: Calendar

	public init(calendar: Calendar = .current, initial: Int = SilenceBudget.dailyMax) {
		self.calendar = calendar
		self.remaining = initial
		self.lastResetDay = calendar.startOfDay(for: Date())
	}

	/// Try to spend one token to surface a proactive card / haptic / TTS.
	/// Returns `true` if the surface is allowed (and the token was deducted),
	/// `false` if the daily budget is exhausted.
	@discardableResult
	public func spend(reason: String = "") -> Bool {
		rolloverIfNewDay()
		guard remaining > 0 else { return false }
		remaining -= 1
		return true
	}

	/// Refund a token because the user marked the surface as useful.
	/// Capped at `dailyMax`.
	public func refund(reason: String = "") {
		rolloverIfNewDay()
		remaining = min(remaining + 1, Self.dailyMax)
	}

	/// Force-reset to the daily maximum. Use only for explicit user action
	/// in Settings — production rollover is handled by `rolloverIfNewDay`.
	public func resetForNewDay() {
		remaining = Self.dailyMax
		lastResetDay = calendar.startOfDay(for: Date())
	}

	private func rolloverIfNewDay() {
		let today = calendar.startOfDay(for: Date())
		if today != lastResetDay {
			remaining = Self.dailyMax
			lastResetDay = today
		}
	}
}
