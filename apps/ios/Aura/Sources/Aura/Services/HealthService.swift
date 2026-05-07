// HealthService.swift
// HealthKit reader stub — HRV (RMSSD), sleep, HR, steps. Mirrors the Swift
// snippet in technical_spec.md §10.1, expanded to cover all four metrics
// the Wellness agent needs. All async, all error-typed.
//
// Production wiring: the Wellness agent calls into this service every five
// minutes via a BGAppRefreshTask. None of the reads persist raw samples
// outside the rolling Load Score window.
#if canImport(HealthKit)
import Foundation
import HealthKit

public actor HealthService {
	private let store = HKHealthStore()

	public init() {}

	public enum HealthServiceError: Error {
		case unavailable
		case notAuthorized
		case queryFailed(Error)
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

	public func requestPermissions() async throws {
		guard HKHealthStore.isHealthDataAvailable() else {
			throw HealthServiceError.unavailable
		}
		try await store.requestAuthorization(toShare: [], read: readTypes)
	}

	/// Average RMSSD over the requested window in milliseconds.
	public func recentRMSSD(window: TimeInterval = 5 * 60) async throws -> Double? {
		try await averageQuantity(
			type: HKQuantityType(.heartRateVariabilitySDNN),
			unit: HKUnit.secondUnit(with: .milli),
			window: window
		)
	}

	/// Average resting / current heart rate over the requested window in BPM.
	public func recentHeartRate(window: TimeInterval = 5 * 60) async throws -> Double? {
		try await averageQuantity(
			type: HKQuantityType(.heartRate),
			unit: HKUnit.count().unitDivided(by: .minute()),
			window: window
		)
	}

	/// Total step count in the requested window.
	public func steps(window: TimeInterval = 24 * 60 * 60) async throws -> Double? {
		try await sumQuantity(
			type: HKQuantityType(.stepCount),
			unit: HKUnit.count(),
			window: window
		)
	}

	/// Total minutes asleep in the most recent main sleep session.
	public func sleepMinutesLastNight() async throws -> Double? {
		guard let type = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return nil }
		let calendar = Calendar.current
		let now = Date()
		let start = calendar.date(byAdding: .hour, value: -16, to: now) ?? now
		let predicate = HKQuery.predicateForSamples(withStart: start, end: now, options: .strictEndDate)
		return try await withCheckedThrowingContinuation { cont in
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
				let asleep = (samples as? [HKCategorySample])?
					.filter { $0.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue }
				let totalSeconds = asleep?.reduce(0) { $0 + $1.endDate.timeIntervalSince($1.startDate) } ?? 0
				cont.resume(returning: totalSeconds > 0 ? totalSeconds / 60 : nil)
			}
			store.execute(query)
		}
	}

	private func averageQuantity(
		type: HKQuantityType,
		unit: HKUnit,
		window: TimeInterval
	) async throws -> Double? {
		let end = Date()
		let start = end.addingTimeInterval(-window)
		let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictEndDate)
		return try await withCheckedThrowingContinuation { cont in
			let query = HKSampleQuery(
				sampleType: type,
				predicate: predicate,
				limit: 100,
				sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]
			) { _, samples, error in
				if let error {
					cont.resume(throwing: HealthServiceError.queryFailed(error))
					return
				}
				let values = (samples as? [HKQuantitySample])?
					.map { $0.quantity.doubleValue(for: unit) } ?? []
				cont.resume(returning: values.isEmpty ? nil : values.reduce(0, +) / Double(values.count))
			}
			store.execute(query)
		}
	}

	private func sumQuantity(
		type: HKQuantityType,
		unit: HKUnit,
		window: TimeInterval
	) async throws -> Double? {
		let end = Date()
		let start = end.addingTimeInterval(-window)
		let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictEndDate)
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
				let total = statistics?.sumQuantity()?.doubleValue(for: unit)
				cont.resume(returning: total)
			}
			store.execute(query)
		}
	}
}
#else
import Foundation

public actor HealthService {
	public init() {}
	public func requestPermissions() async throws {}
	public func recentRMSSD(window: TimeInterval = 300) async throws -> Double? { nil }
	public func recentHeartRate(window: TimeInterval = 300) async throws -> Double? { nil }
	public func steps(window: TimeInterval = 86_400) async throws -> Double? { nil }
	public func sleepMinutesLastNight() async throws -> Double? { nil }
}
#endif
