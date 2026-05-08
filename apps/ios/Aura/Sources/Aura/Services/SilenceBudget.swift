// SilenceBudget.swift
// Implements the Silence Budget state from plan.md §1.2.
// Default daily quota: 3 tokens. Decrement on every proactive surface.
// Refund when the user taps "useful" on the surfaced card. Persisted to
// `UserDefaults` and mirrored to `NSUbiquitousKeyValueStore` so the budget
// survives between iPhone, iPad, and Mac. A midnight reset is scheduled via
// `UNUserNotificationCenter` and `BGAppRefreshTaskRequest`.
import Foundation
#if canImport(Combine)
import Combine
#endif
#if canImport(UserNotifications)
import UserNotifications
#endif
#if canImport(BackgroundTasks)
import BackgroundTasks
#endif

@available(iOS 17.0, macOS 14.0, *)
public final class SilenceBudget: NSObject, ObservableObject {
	public static let dailyMax: Int = 3

	/// Background-refresh identifier registered in Info.plist.
	public static let refreshTaskIdentifier = "com.galaxybrain.aura.refresh"
	public static let processingTaskIdentifier = "com.galaxybrain.aura.processing"

	private static let remainingKey = "aura.silenceBudget.remaining"
	private static let lastResetKey = "aura.silenceBudget.lastReset"
	private static let spentKey     = "aura.silenceBudget.spent"

	/// Audit row for one token spend.
	public struct SpentEntry: Codable, Equatable, Identifiable {
		public let id: UUID
		public let reason: String
		public let date: Date

		public init(id: UUID = UUID(), reason: String, date: Date = Date()) {
			self.id = id
			self.reason = reason
			self.date = date
		}
	}

	@Published public private(set) var remaining: Int
	@Published public private(set) var lastResetDay: Date
	@Published public private(set) var spentToday: [SpentEntry]

	private let calendar: Calendar
	private let defaults: UserDefaults
	private let kvs: NSUbiquitousKeyValueStore?

	public init(
		calendar: Calendar = .current,
		defaults: UserDefaults = .standard,
		kvs: NSUbiquitousKeyValueStore? = .default,
		initial: Int = SilenceBudget.dailyMax
	) {
		self.calendar = calendar
		self.defaults = defaults
		self.kvs = kvs

		let storedRemaining = defaults.object(forKey: Self.remainingKey) as? Int
		let storedReset = defaults.object(forKey: Self.lastResetKey) as? Date

		self.remaining = storedRemaining ?? initial
		self.lastResetDay = storedReset ?? calendar.startOfDay(for: Date())
		if let data = defaults.data(forKey: Self.spentKey),
		   let decoded = try? JSONDecoder().decode([SpentEntry].self, from: data) {
			self.spentToday = decoded
		} else {
			self.spentToday = []
		}

		super.init()

		// Pull a newer iCloud value if the device just came online.
		if let kvs {
			kvs.synchronize()
			if let cloudRemaining = kvs.object(forKey: Self.remainingKey) as? Int,
			   let cloudReset = kvs.object(forKey: Self.lastResetKey) as? Double {
				let cloudDate = Date(timeIntervalSince1970: cloudReset)
				if cloudDate > self.lastResetDay {
					self.remaining = cloudRemaining
					self.lastResetDay = cloudDate
				}
			}
			NotificationCenter.default.addObserver(
				forName: NSUbiquitousKeyValueStore.didChangeExternallyNotification,
				object: kvs,
				queue: .main
			) { [weak self] _ in
				self?.cloudChanged()
			}
		}

		rolloverIfNewDay()
	}

	/// Try to spend one token to surface a proactive card / haptic / TTS.
	@discardableResult
	public func spend(reason: String = "") -> Bool {
		rolloverIfNewDay()
		guard remaining > 0 else { return false }
		remaining -= 1
		spentToday.append(SpentEntry(reason: reason))
		persist()
		return true
	}

	/// Refund a token (capped at `dailyMax`) because the user marked the
	/// surface as useful. Drop the matching audit row if we still have it.
	public func refund(reason: String = "") {
		rolloverIfNewDay()
		remaining = min(remaining + 1, Self.dailyMax)
		if let idx = spentToday.lastIndex(where: { $0.reason == reason }) {
			spentToday.remove(at: idx)
		}
		persist()
	}

	/// Manual reset (Settings → Reset budget). Production rollover happens
	/// in `rolloverIfNewDay()`.
	public func resetForNewDay() {
		remaining = Self.dailyMax
		lastResetDay = calendar.startOfDay(for: Date())
		spentToday.removeAll()
		persist()
	}

	/// Schedule a midnight notification that rolls the day over and reminds
	/// the user the next day's budget is fresh.
	@MainActor
	public func scheduleMidnightReset() {
		#if canImport(UserNotifications)
		let center = UNUserNotificationCenter.current()
		Task {
			_ = try? await center.requestAuthorization(options: [.alert, .badge, .sound])
			let content = UNMutableNotificationContent()
			content.title = "Silence budget reset"
			content.body = "You have \(Self.dailyMax) tokens for today."
			content.sound = nil

			let cal = Calendar.current
			var components = cal.dateComponents([.year, .month, .day], from: Date())
			components.day = (components.day ?? 0) + 1
			components.hour = 0
			components.minute = 1
			let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
			let request = UNNotificationRequest(
				identifier: "aura.silenceBudget.midnight",
				content: content,
				trigger: trigger
			)
			try? await center.add(request)
		}
		#endif
	}

	/// Register both the BGAppRefreshTask (light, foreground-eligible) and the
	/// BGProcessingTask (heavy, nightly) the agents need.
	public static func registerBackgroundTasks(refresh: @escaping () -> Void, process: @escaping () -> Void) {
		#if canImport(BackgroundTasks)
		BGTaskScheduler.shared.register(
			forTaskWithIdentifier: refreshTaskIdentifier,
			using: nil
		) { task in
			refresh()
			task.setTaskCompleted(success: true)
		}
		BGTaskScheduler.shared.register(
			forTaskWithIdentifier: processingTaskIdentifier,
			using: nil
		) { task in
			process()
			task.setTaskCompleted(success: true)
		}
		#endif
	}

	/// Submit the next refresh + processing task. Call from
	/// `applicationDidEnterBackground` and at app launch.
	public static func scheduleNextBackgroundWork() {
		#if canImport(BackgroundTasks)
		let refreshRequest = BGAppRefreshTaskRequest(identifier: refreshTaskIdentifier)
		refreshRequest.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
		try? BGTaskScheduler.shared.submit(refreshRequest)

		let processingRequest = BGProcessingTaskRequest(identifier: processingTaskIdentifier)
		processingRequest.requiresNetworkConnectivity = false
		processingRequest.requiresExternalPower = false
		// Run after midnight so the rollover + nightly memory chores fire.
		var comps = Calendar.current.dateComponents([.year, .month, .day], from: Date())
		comps.day = (comps.day ?? 0) + 1
		comps.hour = 2
		processingRequest.earliestBeginDate = Calendar.current.date(from: comps)
		try? BGTaskScheduler.shared.submit(processingRequest)
		#endif
	}

	private func cloudChanged() {
		guard let kvs else { return }
		kvs.synchronize()
		if let cloudRemaining = kvs.object(forKey: Self.remainingKey) as? Int {
			self.remaining = cloudRemaining
		}
	}

	private func rolloverIfNewDay() {
		let today = calendar.startOfDay(for: Date())
		if today != lastResetDay {
			remaining = Self.dailyMax
			lastResetDay = today
			spentToday.removeAll()
			persist()
		}
	}

	private func persist() {
		defaults.set(remaining, forKey: Self.remainingKey)
		defaults.set(lastResetDay, forKey: Self.lastResetKey)
		if let data = try? JSONEncoder().encode(spentToday) {
			defaults.set(data, forKey: Self.spentKey)
		}
		if let kvs {
			kvs.set(remaining, forKey: Self.remainingKey)
			kvs.set(lastResetDay.timeIntervalSince1970, forKey: Self.lastResetKey)
			kvs.synchronize()
		}
	}
}
