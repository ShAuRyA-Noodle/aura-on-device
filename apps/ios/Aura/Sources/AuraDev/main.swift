// AuraDev/main.swift
// Tiny CLI driver for SPM-only smoke-tests on macOS. Encodes the sample
// Reasoning Trace and prints it. Used to verify the Codable round-trip
// without launching the iOS simulator.
import Foundation
#if canImport(Aura)
import Aura
#endif

if #available(macOS 14.0, *) {
	let trace = Trace.sampleMorningBrief
	if let json = trace.prettyJSON {
		print(json)
	} else {
		print("Failed to encode sample trace.")
	}
} else {
	print("AuraDev requires macOS 14 or later.")
}
