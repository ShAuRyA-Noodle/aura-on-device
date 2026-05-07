// swift-tools-version:5.10
// Package.swift — Aura iOS reference build.
//
// This package declares the Aura library and a thin executable target so that
// the team can develop the agent and view code outside of Xcode (via
// `swift build` on macOS) and drop the same `Sources/Aura/` tree into a fresh
// Xcode 16 multiplatform App project for device builds. See README.md.
import PackageDescription

let package = Package(
	name: "Aura",
	platforms: [
		.iOS(.v17),
		.macOS(.v14)
	],
	products: [
		.library(
			name: "Aura",
			targets: ["Aura"]
		),
		.executable(
			name: "AuraDev",
			targets: ["AuraDev"]
		)
	],
	dependencies: [
		.package(
			url: "https://github.com/google/GoogleSignIn-iOS",
			from: "7.1.0"
		),
		.package(
			url: "https://github.com/apple/swift-collections",
			from: "1.1.0"
		),
		.package(
			url: "https://github.com/kishikawakatsumi/KeychainAccess",
			from: "4.2.2"
		)
	],
	targets: [
		.target(
			name: "Aura",
			dependencies: [
				.product(name: "GoogleSignIn", package: "GoogleSignIn-iOS"),
				.product(name: "GoogleSignInSwift", package: "GoogleSignIn-iOS"),
				.product(name: "Collections", package: "swift-collections"),
				.product(name: "KeychainAccess", package: "KeychainAccess")
			],
			path: "Sources/Aura",
			exclude: ["Resources/Info.plist"],
			resources: [
				.process("Resources/Assets.xcassets")
			]
		),
		.executableTarget(
			name: "AuraDev",
			dependencies: ["Aura"],
			path: "Sources/AuraDev"
		),
		.testTarget(
			name: "AuraTests",
			dependencies: ["Aura"],
			path: "Tests/AuraTests"
		)
	]
)
