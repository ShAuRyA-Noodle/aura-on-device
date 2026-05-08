# Aura iOS — build commands

The agent sandbox does not have Xcode installed, only Apple Command Line
Tools. The team runs the commands below on a Mac with Xcode 16+ installed.

All commands assume `cd apps/ios/Aura`.

## One-time tools

```bash
brew install xcodegen
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
xcodebuild -version  # expect Xcode 16.x
```

## Generate the Xcode project

```bash
xcodegen generate
```

This consumes `project.yml` and writes `Aura.xcodeproj`. Re-run after every
change to `project.yml`. The project file is git-ignored — do not commit.

## Sanity-check the schemes

```bash
xcodebuild -list -project Aura.xcodeproj
```

Expect a `Aura` target, an `AuraTests` target, and a single `Aura` scheme.

## Build for the iPhone 17 / iOS 18 simulator

```bash
xcodebuild \
  -project Aura.xcodeproj \
  -scheme Aura \
  -destination 'generic/platform=iOS Simulator' \
  -configuration Debug \
  build \
  CODE_SIGNING_ALLOWED=NO \
  2>&1 | tail -50
```

Expected last line on success: `** BUILD SUCCEEDED **`.

If you get `error: unable to find a destination matching the provided
destination specifier`, run `xcrun simctl list runtimes` and use the exact
runtime string (for example `'platform=iOS Simulator,name=iPhone 17,OS=18.0'`).

## Build for a physical device

1. Open `Aura.xcodeproj` in Xcode.
2. Target → **Signing & Capabilities** → set **Team** to your Apple Developer
   team. The placeholder `DEVELOPMENT_TEAM` in `project.yml` is empty.
3. Plug in the iPhone, select it as the run destination.
4. Cmd-R.

The first launch will prompt for HealthKit, Calendar, Notifications, and
Local Network permissions. The Onboarding sheet steps through each
rationale before the system prompt appears.

## Build for TestFlight

```bash
xcodebuild \
  -project Aura.xcodeproj \
  -scheme Aura \
  -configuration Release \
  -archivePath build/Aura.xcarchive \
  archive

xcodebuild \
  -exportArchive \
  -archivePath build/Aura.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/Export
```

`ExportOptions.plist` is a small file the team keeps next to the project;
ask Shaurya for the latest copy.

## Run the SPM-only smoke test

```bash
swift build               # builds the Aura library on macOS
swift run AuraDev         # encodes the sample Reasoning Trace and prints it
swift test                # XCTest target
```

`AuraMain.swift`, `AuraConfig.xcconfig`, and `Resources/Aura.entitlements`
are excluded from the SPM build because the SPM target ships as a library.

## Trace bridge

The Mac runs the FastAPI orchestrator on port 8000. With the iPhone
USB-tethered, the simulator and the device both reach the bridge at
`http://localhost:8000` because Xcode forwards usbmuxd. Override
`AuraBridge.shared.baseURL` from the in-app Settings panel for Wi-Fi mode.

## Troubleshooting

* `Could not resolve package dependencies`: run `swift package
  reset` then `xcodegen generate` again.
* `Sandbox: deny(1) file-write-create`: the sandbox you ran in did not
  have write permission to the source tree. Run from a fresh terminal.
* `error: HealthKit is not available`: simulator builds for iPad cannot
  read Health. Pick the iPhone simulator.
