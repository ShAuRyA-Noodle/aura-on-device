# ADR-0006 — Platform Strategy: Apple-only Phase 1+2, Galaxy Production Target

## Status

Accepted (2026-05-07). Source: `plan.md` §0, §21, §35; `technical_spec.md` §14.

## Context

The submission is to Samsung EnnovateX 2026, judged primarily by Samsung R&D India, One UI / Bixby PMs, and Galaxy ecosystem leads. The team owns Apple devices (iPhone, Apple Watch, AirPods, Mac) and one Windows training laptop (Alienware M16 R1, RTX 4080 Laptop GPU 12 GB VRAM). The team owns no Galaxy device. The total project budget is ₹2,000, which precludes a Galaxy phone purchase.

This is the highest-risk constraint in the plan (`plan.md` §27 R1, R10). It is also non-negotiable.

Constraints:

- The plan locks Apple-only build (`plan.md` §0, §35 #5).
- The architecture must remain platform-agnostic at the API layer (`plan.md` §10.1 platform parity table; deck slide 4a).
- The team will not buy or borrow a Galaxy device for Phase 1 or Phase 2.
- The team must not show iOS screenshots wrapped in Galaxy device frames, or claim Galaxy Watch HRV numbers measured on an Apple Watch (`plan.md` §21.3).

Forces:

- A Samsung judge expects to see Galaxy ecosystem fluency on slide 4 — Galaxy AI, Knox, Health Connect, One UI, Bixby integration points.
- A Samsung judge will penalise a vendor for marketing-voice cross-platform claims that don't ship.
- The Phase 3 demo, if reached, may have a venue device available; the deck's opening line must stand whether the demo runs on iPhone or Galaxy.

## Decision

Aura is built and demonstrated on Apple substrate for Phase 1 and Phase 2. The Galaxy ecosystem is the production target. The submission frames this honestly:

- **Phase 1 (Blueprint).** No device required. Architecture diagram on slide 4 names Galaxy AI, Knox, Health Connect, One UI, Bixby integration points as production targets. Plausibility table (slide 4a) maps every iOS API 1:1 to its Android counterpart.
- **Phase 2 (Prototype, if shortlisted).** Pilot runs on iOS via TestFlight, n=30 college users (`plan.md` §23). Galaxy port shown via Android emulator on Mac (Pixel + Galaxy AVD images, free): Comms and Wellness agents ported and screen-recorded. Honest framing in any submitted video: "Galaxy port via Android emulator; Apple device for live biometric loop."
- **Phase 3 (Finals).** Demo on iPhone unless a Galaxy device is available at the venue. The opening line is locked (`plan.md` §21.4):
  > "Aura is platform-agnostic. We built the reference on iPhone because that's the device our college owned, and a two-thousand-rupee total budget didn't stretch to a flagship phone. The architecture you see ports to Galaxy via the API table on slide 4. We never claim numbers we did not measure. Now let me show you what we did measure."

The team will:

- Maintain the platform parity table in `plan.md` §10.1 and deck slide 4a.
- Implement an Android emulator port of CommsAgent and WellnessAgent in Phase 2.
- Honour the four "what we never claim" lines from `plan.md` §21.3.

## Consequences

Positive:

- The constraint becomes a credibility beat rather than a hidden gap. Engineer judges respond to honest framing more than to marketing voice.
- The architecture stays clean — every iOS-only path has a documented Android counterpart and a known limit.
- Budget stays at ₹0 for hardware. Total project spend stays at ₹2,000.

Negative / costs:

- Some judges will still mark the Apple-only build as a fit problem; risk R1, R10 in `plan.md` §27.
- The Phase 2 Galaxy demo via emulator is weaker than a live device demo. Mitigated by a screen-recorded port plus the API parity table.
- iOS sandbox blocks SMS read; FinanceAgent's UPI feature is Android-only. Mitigated by manual Gmail-receipt import on iOS during the pilot (`plan.md` §27 R13).

## Alternatives

- **Buy a Galaxy A series mid-tier device (~₹15,000).** Rejected: blows the ₹2,000 budget; Tier C device under ADR-0002 anyway, so reduced-feature build.
- **Borrow a Galaxy device from a friend for the duration of the project.** Considered; held in reserve as a Phase 3 contingency. Cannot be relied on for Phase 2 pilot duration (8–10 weeks).
- **Skip the Apple build, target Android only via emulator.** Rejected: emulator cannot read live HRV from a Watch, breaking the closed-loop biometric wedge that is core to the pitch.
- **Apologise for the constraint in the deck.** Rejected: framing the constraint as a deliberate engineering choice (Apple as the hardest privacy substrate) is more credible than an apology.

End of ADR-0006.
