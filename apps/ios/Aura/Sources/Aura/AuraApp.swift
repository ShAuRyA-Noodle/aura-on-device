// AuraApp.swift
// SwiftUI entrypoint. Three top-level tabs per plan §10.3: Brief, Memory, Settings.
//
// To run inside Xcode: create a fresh multiplatform App project named "Aura",
// drop in this Sources/Aura/ tree, and replace the generated `@main` App
// struct with the one below. SPM-only dev builds use `AuraDev` as the
// executable entrypoint; see Sources/AuraDev/main.swift.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct AuraApp: App {
	@StateObject private var silenceBudget = SilenceBudget()

	public init() {}

	public var body: some Scene {
		WindowGroup {
			RootTabView()
				.environmentObject(silenceBudget)
				.tint(Color("AccentColor"))
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct RootTabView: View {
	@State private var selection: Tab = .brief

	enum Tab: Hashable {
		case brief
		case memory
		case settings
	}

	var body: some View {
		TabView(selection: $selection) {
			MorningBriefView()
				.tabItem {
					Label("Brief", systemImage: "sun.max")
				}
				.tag(Tab.brief)

			MemoryView()
				.tabItem {
					Label("Memory", systemImage: "tray.full")
				}
				.tag(Tab.memory)

			SettingsView()
				.tabItem {
					Label("Settings", systemImage: "gearshape")
				}
				.tag(Tab.settings)
		}
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct SettingsView: View {
	@EnvironmentObject var silenceBudget: SilenceBudget

	var body: some View {
		NavigationStack {
			List {
				Section("Silence Budget") {
					LabeledContent("Tokens remaining today", value: "\(silenceBudget.remaining)/\(SilenceBudget.dailyMax)")
					Button("Reset budget") {
						silenceBudget.resetForNewDay()
					}
				}
				Section("Permissions") {
					Text("HealthKit, Calendar, Notifications — request on first use.")
						.font(.callout)
				}
				Section("About") {
					Text("Aura — Galaxy Brain — Samsung EnnovateX 2026")
						.font(.callout)
				}
			}
			.navigationTitle("Settings")
		}
	}
}
