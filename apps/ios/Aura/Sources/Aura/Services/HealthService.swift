// HealthService.swift
// Real HealthKit reads for HRV (SDNN), sleep, heart rate, and step count.
// Implements technical_spec.md §10.1. All async/await, no completion-handler
// callbacks at the public surface, no force-unwraps. Permission requests go
// through `HKHealthStore.requestAuthorization`.
//
// Production wiring: the Wellness agent calls into this service every five
// minutes via `BGAppRefreshTask`. None of the reads persist raw samples
// outside the rolling Load Score window held by the agent.
#if canImport(HealthKit)
import Foundation
import HealthKit

public actor HealthService {
	private let store = HKHealthStore()

	public init() {}

	public enum HealthServiceError: Error, LocalizedError {
		case unavailable
		case notAuthorized
		case missingType(String)
		case queryFailed(Error)

		public var errorDescription: String? {
			switch self {
			case .unavailable:        return "HealthKit is not available on this device."
			case .notAuthorized:      return "Aura was not granted permission to read Health data."
			case .missingType(let s): return "HealthKit type \(s) is not available on this OS version."
			case .queryFailed(let e): return "Health query failed: \(e.localizedDescription)"
			}
		}
	}

	/// Snapshot used by the Morning Brief view. All values are optional —
	/// missing readings render as em-dashes, never zero.
	public struct Snapshot: Sendable, Equatable {
		public let rmssdMillis: Double?
		public let heartRateBPM: Double?
		public let sleepMinutes: Double?
		public let stepsToday: Double?

		public var sleepHoursDescription: String {
			guard let mins = sleepMinutes, mins > 0 else { return "—" }
			let h = Int(mins) / 60
			let m = Int(mins) % 60
			return "\(h) h \(m) m"
		}

		public var rmssdDescription: String {
			guard let v = rmssdMillis else { return "—" }
			return String(format: "%.0f ms", v)
		}

		public var heartRateDescription: String {
			guard let v = heartRateBPM else { return "—" }
			return String(format: "%.0f bpm", v)
		}

		public var stepsDescription: String {
			guard let v = stepsToday else { return "—" }
			return "\(Int(v))"
		}
	}

	private var readTypes: Set<HKObjectType> {
		var types: Set<HKObjectType> = [
			HKQuantityType(.heartRateVariabilitySDNN),
			HKQuantityType(.heartRate),
			HKQuantityType(.stepCount)
		]
		if let sleep = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) {
			types.insert(sleep)
		}
		return types
	}

	/// Ask the user for read access to the four metrics Aura uses.
	public func requestPermissions() async throws {
		guard HKHealthStore.isHealthDataAvailable() else {
			throw HealthServiceError.unavailable
		}
		try await store.requestAuthorization(toShare: [], read: readTypes)
	}

	/// Fetch all four metrics in parallel and return a snapshot.
	public func snapshot() async -> Snapshot {
		async let rmssd = (try? await recentRMSSD()) ?? nil
		async let hr = (try? await recentHeartRate()) ?? nil
		async let sleep = (try? await sleepMinutesLastNight()) ?? nil
		async let steps = (try? await stepsToday()) ?? nil
		return await Snapshot(
			rmssdMillis: rmssd,
			heartRateBPM: hr,
			sleepMinutes: sleep,
			stepsToday: steps
		)
	}

	/// Average RMSSD over the requested window in milliseconds.
	public func recentRMSSD(window: TimeInterval = 5 * 60) async throws -> Double? {
		try await averageQuantity(
			type: HKQuantityType(.heartRateVariabilitySDNN),
			unit: HKUnit.secondUnit(with: .milli),
			window: window
		)
	}

	/// Average heart rate over the requested window in BPM.
	public func recentHeartRate(window: TimeInterval = 5 * 60) async throws -> Double? {
		try await averageQuantity(
			type: HKQuantityType(.heartRate),
			unit: HKUnit.count().unitDivided(by: .minute()),
			window: window
		)
	}

	/// Step count for the current calendar day.
	public func stepsToday() async throws -> Double? {
		let cal = Calendar.current
		let start = cal.startOfDay(for: Date())
		return try await sumQuantity(
			type: HKQuantityType(.stepCount),
			unit: HKUnit.count(),
			start: start,
			end: Date()
		)
	}

	/// Total step count in the requested window (kept for parity with spec).
	public func steps(window: TimeInterval = 24 * 60 * 60) async throws -> Double? {
		let end = Date()
		let start = end.addingTimeInterval(-window)
		return try await sumQuantity(
			type: HKQuantityType(.stepCount),
			unit: HKUnit.count(),
			start: start,
			end: end
		)
	}

	/// Total minutes asleep in the most recent main sleep session.
	public func sleepMinutesLastNight() async throws -> Double? {
		guard let type = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else {
			throw HealthServiceError.missingType("sleepAnalysis")
		}
		let cal = Calendar.current
		let now = Date()
		let start = cal.date(byAdding: .hour, value: -16, to: now) ?? now
		let predicate = HKQuery.predicateForSamples(
			withStart: start,
			end: now,
			options: .strictEndDate
		)
		let samples: [HKCategorySample] = try await withCheckedThrowingContinuation { cont in
			let query = HKSampleQuery(
				sampleType: type,
				predicate: predicate,
				limit: HKObjectQueryNoLimit,
				sortDescriptors: nil
			) { _, samples, error in
				if let error {
					cont.resume(throwing: HealthServiceError.queryFailed(error))
					return
				}
				cont.resume(returning: (samples as? [HKCategorySample]) ?? [])
			}
			store.execute(query)
		}
		let asleepValues: Set<Int> = [
			HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue,
			HKCategoryValueSleepAnalysis.asleepREM.rawValue,
			HKCategoryValueSleepAnalysis.asleepCore.rawValue,
			HKCategoryValueSleepAnalysis.asleepDeep.rawValue
		]
		let asleep = samples.filter { asleepValues.contains($0.value) }
		let totalSeconds = asleep.reduce(0.0) { acc, s in
			acc + s.endDate.timeIntervalSince(s.startDate)
		}
		return totalSeconds > 0 ? totalSeconds / 60 : nil
	}

	private func averageQuantity(
		type: HKQuantityType,
		unit: HKUnit,
		window: TimeInterval
	) async throws -> Double? {
		let end = Date()
		let start = end.addingTimeInterval(-window)
		let predicate = HKQuery.predicateForSamples(
			withStart: start,
			end: end,
			options: .strictEndDate
		)
		return try await withCheckedThrowingContinuation { cont in
			let query = HKSampleQuery(
				sampleType: type,
				predicate: predicate,
				limit: 100,
				sortDescriptors: [
					NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
				]
			) { _, samples, error in
				if let error {
					cont.resume(throwing: HealthServiceError.queryFailed(error))
					return
				}
				let values = (samples as? [HKQuantitySample])?
					.map { $0.quantity.doubleValue(for: unit) } ?? []
				cont.resume(
					returning: values.isEmpty ? nil : values.reduce(0, +) / Double(values.count)
				)
			}
			store.execute(query)
		}
	}

	private func sumQuantity(
		type: HKQuantityType,
		unit: HKUnit,
		start: Date,
		end: Date
	) async throws -> Double? {
		let predicate = HKQuery.predicateForSamples(
			withStart: start,
			end: end,
			options: .strictEndDate
		)
		return try await withCheckedThrowingContinuation { cont in
			let query = HKStatisticsQuery(
				quantityType: type,
				quantitySamplePredicate: predicate,
				options: .cumulativeSum
			) { _, statistics, error in
				if let error {
					cont.resume(throwing: HealthServiceError.queryFailed(error))
					return
				}
				cont.resume(returning: statistics?.sumQuantity()?.doubleValue(for: unit))
			}
			store.execute(query)
		}
	}
}
#else
import Foundation

public actor HealthService {
	public init() {}

	public struct Snapshot: Sendable, Equatable {
		public let rmssdMillis: Double?
		public let heartRateBPM: Double?
		public let sleepMinutes: Double?
		public let stepsToday: Double?

		public var sleepHoursDescription: String { "—" }
		public var rmssdDescription: String { "—" }
		public var heartRateDescription: String { "—" }
		public var stepsDescription: String { "—" }
	}

	public func requestPermissions() async throws {}
	public func snapshot() async -> Snapshot {
		Snapshot(rmssdMillis: nil, heartRateBPM: nil, sleepMinutes: nil, stepsToday: nil)
	}
	public func recentRMSSD(window: TimeInterval = 300) async throws -> Double? { nil }
	public func recentHeartRate(window: TimeInterval = 300) async throws -> Double? { nil }
	public func steps(window: TimeInterval = 86_400) async throws -> Double? { nil }
	public func stepsToday() async throws -> Double? { nil }
	public func sleepMinutesLastNight() async throws -> Double? { nil }
}
#endif
