# Aura — iOS reference build

This directory holds the SwiftUI source tree for the Aura iOS app. It is
shipped as a Swift Package so that it can be developed and smoke-tested
from the command line on macOS, then dropped into a fresh Xcode 16
project for device builds and TestFlight distribution.

## Layout

```
Aura/
├── Package.swift             # SPM manifest; declares deps + targets
├── Sources/
│   ├── Aura/                 # Library — App, Views, Models, Services
│   │   ├── AuraApp.swift
│   │   ├── Views/
│   │   ├── Models/
│   │   ├── Services/
│   │   └── Resources/
│   │       ├── Info.plist
│   │       └── Assets.xcassets/
│   └── AuraDev/main.swift    # Tiny CLI for `swift run AuraDev`
└── Tests/AuraTests/          # XCTest target
```

## Drop into Xcode 16 — step by step

1. In Xcode 16: `File → New → Project → Multiplatform → App`. Name it
   `Aura`. Set the bundle identifier to `ai.aura`. Language: Swift.
   Interface: SwiftUI. Storage: None.
2. Close the project. Open the project folder in Finder.
3. Replace the auto-generated `AuraApp.swift` with the one from
   `Sources/Aura/AuraApp.swift`. Add the `@main` attribute back to
   `AuraApp` (it is omitted here because the library target cannot
   declare an entrypoint).
4. Drag `Sources/Aura/Views/`, `Sources/Aura/Models/`,
   `Sources/Aura/Services/`, and `Sources/Aura/Resources/Assets.xcassets`
   into the Xcode project navigator. Tick "Copy items if needed" and
   ensure they are added to the `Aura` target.
5. Replace the auto-generated `Info.plist` with
   `Sources/Aura/Resources/Info.plist`, or copy the usage description
   keys (`NSHealthShareUsageDescription`, `NSCalendarsUsageDescription`,
   `NSUserNotificationsUsageDescription`, etc.) into the target's
   "Info" tab.
6. In the target's "Signing & Capabilities" tab, add:
   - HealthKit
   - Background Modes (Background fetch, Background processing)
   - Push Notifications (for the local notification surface)
7. Add Swift Package dependencies via `File → Add Package Dependencies`:
   - `https://github.com/google/GoogleSignIn-iOS` (7.1+)
   - `https://github.com/apple/swift-collections` (1.1+)
   - `https://github.com/kishikawakatsumi/KeychainAccess` (4.2+)
8. Configure the Google Sign-In `GIDClientID` in
   `GoogleService-Info.plist`. This file must not be committed; see
   `.gitignore`.
9. Build and run on a device (Watch HRV requires a real iPhone +
   Apple Watch). Simulator builds work for everything except HealthKit.

## Smoke-test from the command line

```bash
cd apps/ios/Aura
swift build
swift run AuraDev
swift test
```

The `AuraDev` executable encodes the sample Reasoning Trace and prints
it; this verifies the Codable round-trip without launching Xcode.

## Conventions

- Tabs for indentation per `.editorconfig`.
- Every public type has a one-paragraph comment naming the spec section it
  implements (`technical_spec.md §10.1`, etc.).
- Services are `actor`s. UI state is on the main actor.
- `@available(iOS 17.0, macOS 14.0, *)` on every SwiftUI type so SPM
  builds on macOS for tests.
