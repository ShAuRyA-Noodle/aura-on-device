// Trace.swift
// Codable mirror of the Reasoning Trace JSON Schema in
// technical_spec.md §4.6. The struct must round-trip with the schema
// without loss. Keep field names aligned with the JSON keys.
import Foundation

public struct Trace: Codable, Equatable, Identifiable {
	public let traceId: String
	public let ts: String
	public let trigger: Trigger
	public let signals: [Signal]
	public let candidates: [Candidate]
	public let chosen: String
	public let rationale: String
	public let rationaleSource: RationaleSource?
	public let confirmRequired: Bool
	public let outcome: Outcome
	public let redactions: [String]?

	public var id: String { traceId }

	public enum CodingKeys: String, CodingKey {
		case traceId = "trace_id"
		case ts
		case trigger
		case signals
		case candidates
		case chosen
		case rationale
		case rationaleSource = "rationale_source"
		case confirmRequired = "confirm_required"
		case outcome
		case redactions
	}

	public enum RationaleSource: String, Codable {
		case template
		case llm
	}

	public enum Outcome: String, Codable {
		case pending
		case confirmed
		case dismissed
		case timedOut = "timed_out"
		case executedAuto = "executed_auto"
		case failed
	}

	public struct Trigger: Codable, Equatable {
		public let source: String
		public let value: AnyCodable

		public init(source: String, value: AnyCodable) {
			self.source = source
			self.value = value
		}
	}

	public struct Signal: Codable, Equatable, Identifiable {
		public let k: String
		public let v: AnyCodable

		public var id: String { k }

		public init(k: String, v: AnyCodable) {
			self.k = k
			self.v = v
		}

		public var displayValue: String {
			v.displayString
		}
	}

	public struct Candidate: Codable, Equatable {
		public let kind: String
		public let score: Double
		public let components: Components?
		public let confirmRequired: Bool

		public enum CodingKeys: String, CodingKey {
			case kind
			case score
			case components
			case confirmRequired = "confirm_required"
		}

		public struct Components: Codable, Equatable {
			public let util: Double?
			public let cost: Double?
			public let recent: Double?
			public let dnd: Double?
		}
	}
}

public extension Trace {
	var prettyJSON: String? {
		let encoder = JSONEncoder()
		encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
		guard let data = try? encoder.encode(self) else { return nil }
		return String(data: data, encoding: .utf8)
	}
}

// MARK: - AnyCodable
// Minimal type-erased Codable wrapper so Trigger.value and Signal.v can hold
// any JSON-allowed value. Keeps the Codable round-trip lossless.
public struct AnyCodable: Codable, Equatable {
	public let value: Any

	public init(_ value: Any) {
		self.value = value
	}

	public init(from decoder: Decoder) throws {
		let container = try decoder.singleValueContainer()
		if container.decodeNil() {
			value = NSNull()
		} else if let b = try? container.decode(Bool.self) {
			value = b
		} else if let i = try? container.decode(Int.self) {
			value = i
		} else if let d = try? container.decode(Double.self) {
			value = d
		} else if let s = try? container.decode(String.self) {
			value = s
		} else if let arr = try? container.decode([AnyCodable].self) {
			value = arr.map { $0.value }
		} else if let dict = try? container.decode([String: AnyCodable].self) {
			value = dict.mapValues { $0.value }
		} else {
			throw DecodingError.dataCorruptedError(
				in: container,
				debugDescription: "Unsupported JSON type for AnyCodable."
			)
		}
	}

	public func encode(to encoder: Encoder) throws {
		var container = encoder.singleValueContainer()
		switch value {
		case is NSNull:
			try container.encodeNil()
		case let b as Bool:
			try container.encode(b)
		case let i as Int:
			try container.encode(i)
		case let d as Double:
			try container.encode(d)
		case let s as String:
			try container.encode(s)
		case let arr as [Any]:
			try container.encode(arr.map { AnyCodable($0) })
		case let dict as [String: Any]:
			try container.encode(dict.mapValues { AnyCodable($0) })
		default:
			throw EncodingError.invalidValue(
				value,
				EncodingError.Context(
					codingPath: container.codingPath,
					debugDescription: "Unsupported value type for AnyCodable."
				)
			)
		}
	}

	public var displayString: String {
		switch value {
		case is NSNull: return "null"
		case let b as Bool: return b ? "true" : "false"
		case let i as Int: return String(i)
		case let d as Double: return String(d)
		case let s as String: return s
		case let arr as [Any]: return "[\(arr.count) items]"
		case let dict as [String: Any]: return "{\(dict.count) keys}"
		default: return String(describing: value)
		}
	}

	public static func == (lhs: AnyCodable, rhs: AnyCodable) -> Bool {
		String(describing: lhs.value) == String(describing: rhs.value)
	}
}

// MARK: - Sample data
public extension Trace {
	/// Sample matching technical_spec.md §5.6 (a) — Morning Brief.
	static let sampleMorningBrief = Trace(
		traceId: "tr_a8c12fb091e3",
		ts: "2026-05-07T07:45:02+05:30",
		trigger: Trigger(source: "phone_unlock", value: AnyCodable(["hour": 7.75])),
		signals: [
			Signal(k: "sleep_min_last", v: AnyCodable(312)),
			Signal(k: "travel_min_to_LT3", v: AnyCodable(22)),
			Signal(k: "unread_gmail_24h", v: AnyCodable(12)),
			Signal(k: "prof_email_present", v: AnyCodable(true))
		],
		candidates: [
			Candidate(
				kind: "SHOW_BRIEF",
				score: 0.82,
				components: Candidate.Components(util: 1.10, cost: 0.20, recent: 0.0, dnd: 0.0),
				confirmRequired: false
			),
			Candidate(
				kind: "LEAVE_BY_ALERT",
				score: 0.71,
				components: nil,
				confirmRequired: false
			),
			Candidate(
				kind: "BATCH_DIGEST",
				score: 0.55,
				components: nil,
				confirmRequired: false
			),
			Candidate(
				kind: "do_nothing",
				score: 0.30,
				components: nil,
				confirmRequired: false
			)
		],
		chosen: "SHOW_BRIEF",
		rationale: "Quiz in 75 min, 22 min travel, prof emailed at 23:11. One card.",
		rationaleSource: .template,
		confirmRequired: false,
		outcome: .executedAuto,
		redactions: []
	)
}
