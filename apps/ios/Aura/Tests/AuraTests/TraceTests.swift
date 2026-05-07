// TraceTests.swift
// Round-trip the sample Reasoning Trace through Codable and verify shape.
import XCTest
@testable import Aura

final class TraceTests: XCTestCase {
	func testSampleMorningBriefRoundTrips() throws {
		let original = Trace.sampleMorningBrief
		let encoder = JSONEncoder()
		let decoder = JSONDecoder()
		let data = try encoder.encode(original)
		let decoded = try decoder.decode(Trace.self, from: data)
		XCTAssertEqual(decoded.traceId, original.traceId)
		XCTAssertEqual(decoded.chosen, "SHOW_BRIEF")
		XCTAssertEqual(decoded.candidates.count, original.candidates.count)
		XCTAssertEqual(decoded.outcome, .executedAuto)
	}

	func testTraceIdMatchesSchemaPattern() {
		let trace = Trace.sampleMorningBrief
		let pattern = #"^tr_[a-z0-9]{12}$"#
		let range = trace.traceId.range(of: pattern, options: .regularExpression)
		XCTAssertNotNil(range, "trace_id must match technical_spec.md §4.6 pattern.")
	}
}
