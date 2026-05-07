---
slide: 4a
title: Plausibility & Constraints (extended)
---
## BODY
Twelve capabilities. Two platforms. Three honest limits.
iOS blocks SMS and cross-app notifications.
Android primary, iOS reference. We never claim a kernel hook we don't have.

## SPEAKER NOTES
This is the honest table. Twelve capabilities Aura needs, mapped to Android and iOS APIs. Three places we cannot do on iOS what Android lets us do: SMS read does not exist on iOS, cross-app notifications are limited to our own app on iOS, and DeviceActivity gives us only partial app-launch data. We do not pretend otherwise. Production target is the Galaxy ecosystem with Health Connect as the substrate and Knox vault for memory-graph encryption. iOS reference build proves the algorithms are cross-platform on the hardest privacy substrate first. The line at the bottom is our promise to a Samsung engineer in the room: we will never claim a kernel hook we do not have, never quote a Galaxy Watch HRV number we measured on an Apple Watch, never show an iOS screenshot and call it One UI. That honesty is the credibility beat.

## CITATIONS
[3] Health Connect, [5] UsageStatsManager, [6] NotificationListenerService, [9] HealthKit. iOS DeviceActivity reference doc URL [TEAM TO VERIFY].

## VISUAL BRIEF
Full-width data table. Cols 1-12, single table, no shadow, no header fill, only a 2 px #0E0E0E rule under the header row and 1 px hairlines at 20% opacity between data rows. Header row Inter Tight 18 pt bold tracked +40, sunset-orange underline 4 px under the column Known limit. Capability column Inter Tight 18 pt regular, API columns JetBrains Mono 14 pt. Twelve rows covering app-launch, cross-app notifications, SMS, calendar, health, typing entropy, location, ambient audio level, battery, screen state, ringer, Gmail. Limit cells use a hand-drawn-feel sunset-orange triangle vector when a limit exists, blank when none, followed by 14 pt italic text. Bottom strip cols 1-12: a single Fraunces 32 pt line: We never claim a kernel hook we don't have. Reference: Stripe API tables, Apple HIG reference tables.

## PERSUASION JOB
Trust signal to Engineer and Samsung Exec — the team is honest about the Apple-vs-Samsung gap.
