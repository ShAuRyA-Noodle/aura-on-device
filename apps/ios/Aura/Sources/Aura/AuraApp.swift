// AuraApp.swift
// SwiftUI scene root. Four top-level tabs per plan §10.3 + the live trace
// drawer surface: Brief, Memory, Settings, Trace. The Trace tab subscribes
// to the FastAPI bridge WebSocket (see `AuraBridge`).
//
// To run inside Xcode: the `@main` entry is `AuraAppMain` in
// `AuraMain.swift`. SPM-only dev builds call `AuraApp` from
// `Sources/AuraDev/main.swift`.
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
public struct AuraApp: App {
	@StateObject private var silenceBudget = SilenceBudget()
	@StateObject private var bridge = AuraBridge.shared

	public init() {}

	public var body: some Scene {
		WindowGroup {
			RootTabView()
				.environmentObject(silenceBudget)
				.environmentObject(bridge)
				.tint(Color("AccentColor"))
				.task {
					await bootstrap()
				}
		}
	}

	private func bootstrap() async {
		_ = await bridge.ping()
		await silenceBudget.scheduleMidnightReset()
		SilenceBudget.scheduleNextBackgroundWork()
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct RootTabView: View {
	@State private var selection: Tab = .brief
	@State private var showOnboarding = false
	@AppStorage("aura.onboarded") private var onboarded: Bool = false

	enum Tab: Hashable {
		case brief
		case memory
		case settings
		case trace
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

			LiveTraceView()
				.tabItem {
					Label("Trace", systemImage: "waveform.path.ecg")
				}
				.tag(Tab.trace)

			SettingsView()
				.tabItem {
					Label("Settings", systemImage: "gearshape")
				}
				.tag(Tab.settings)
		}
		.task {
			if !onboarded { showOnboarding = true }
		}
		.sheet(isPresented: $showOnboarding) {
			PermissionFlow(onComplete: { onboarded = true })
		}
	}
}

/// Wraps the streaming `ReasoningTraceView` so it can live inside a tab.
@available(iOS 17.0, macOS 14.0, *)
struct LiveTraceView: View {
	var body: some View {
		ReasoningTraceView()
	}
}

@available(iOS 17.0, macOS 14.0, *)
struct SettingsView: View {
	@EnvironmentObject var silenceBudget: SilenceBudget
	@EnvironmentObject var bridge: AuraBridge
	@State private var showSilenceBudget = false

	var body: some View {
		NavigationStack {
			List {
				Section("Silence Budget") {
					LabeledContent("Tokens remaining today", value: "\(silenceBudget.remaining)/\(SilenceBudget.dailyMax)")
					Button("Open silence budget") {
						showSilenceBudget = true
					}
					Button("Reset budget") {
						silenceBudget.resetForNewDay()
					}
				}
				Section("Bridge") {
					LabeledContent("Status", value: bridge.isConnected ? "live" : "offline")
					LabeledContent("Base URL", value: bridge.baseURL.absoluteString)
					Button("Re-test connection") {
						Task { _ = await bridge.ping() }
					}
				}
				Section("Permissions") {
					Text("HealthKit, Calendar, Notifications — request on first use, or re-trigger from the onboarding sheet.")
						.font(.callout)
				}
				Section("About") {
					Text("Aura — Galaxy Brain — Samsung EnnovateX 2026")
						.font(.callout)
				}
			}
			.navigationTitle("Settings")
			.sheet(isPresented: $showSilenceBudget) {
				SilenceBudgetView()
			}
		}
	}
}
