# ADR-0010 — Pilot Protocol: 8 Qualitative + 30 Quantitative, Unpaid, IRB-Style Consent

## Status

Accepted (2026-05-07). Source: `plan.md` §22, §23, §35 #19; `technical_spec.md` §12.6.

## Context

The EnnovateX brief explicitly requires verifiable raw evidence (recordings, screenshots, survey data) and clearly defined measurement methods. The KPIs are explicit (`plan.md` §22): ≥30% effort reduction, ≥90% task completion, ≥85% AI autonomy quality, ≥4.5/5 satisfaction, measurable stress reduction, ≥60% willingness to pay.

The plan calls for a 30-user quantitative pilot and 8-user qualitative interviews on Thapar campus, drawn from friends and student networks. The team has chosen to run unpaid (`plan.md` §35 #19). Consent must be defensible if a Samsung judge asks for the protocol.

Constraints:

- Budget for incentives: ₹0 (`plan.md` §26).
- Pilot platform: iOS via TestFlight (ADR-0006).
- Pilot duration: Week 8 qualitative, Week 9 quantitative (`plan.md` §24).
- Aura's privacy promise: per-participant aggregated and anonymised data only; no raw personal content centrally stored (`plan.md` §23.5).

Forces:

- A submission with raw CSV in the public repo is materially more credible than one without.
- Unpaid pilot recruiting under-fills if the value-exchange isn't compelling. Mitigation: the participant gets to keep the build, gets a personal stress-correlation report, and gets named in the acknowledgements.
- Phase 2 deliverable requires a working prototype plus 30-user pilot evidence.

## Decision

**Sample size.** The pilot is **8 qualitative + 30 quantitative**. The qualitative sample is a subset of the 30, plus 2 Bangalore-based participants to balance city context. Recruitment buffer is 50% (recruit 45 to get 30 reliable).

**Recruitment.** Posted on Thapar Tech and Design club channels, plus 2nd / 3rd-year course-mate networks. Mixed years and branches, target 50/50 gender, 50/50 hostel/day-scholar. No paid ads.

**Compensation.** Unpaid. Participants receive: the working build for the pilot duration, a one-page personal stress-correlation report at the end, and acknowledgement in the public repo `THANKS.md` (with consent).

**Consent.** Plain-English written consent form (`pilot/consent_form.md` per `plan.md` §19 layout). The form names every signal class Aura reads (HRV, sleep, typing entropy, app-switch rate, notification metadata, calendar events, Gmail metadata, SMS on Android only, location bucketed to 200 m grid), names the on-device-only invariant (ADR-0005), and names the user's wipe and export rights. Explicit per-permission opt-in.

This is **IRB-style** consent — modelled on Belmont-principles informed consent, not formally IRB-approved (the team is not running through Thapar's research ethics committee for this submission). The form discloses the limits of the protocol: no ethics-committee oversight, the team is the recruiter and analyst, the team is the developer with bias.

**Qualitative protocol** (`plan.md` §23.3). 60-minute semi-structured interview after 7 days of use. Daily diary entries, one per day, three questions, 90 seconds. Two coders, thematic analysis, iterative.

**Quantitative protocol** (`plan.md` §23.4). Five standardised tasks (`plan.md` §22.2), randomised order. Pre-survey: demographics + status quo apps and pain points. Post-survey: Likert satisfaction, Van Westendorp WTP, NPS.

**Statistical reporting** (`plan.md` §22.3). Means + 95% CI. Paired t-test or Wilcoxon for baseline-vs-prototype task differences. Cohen's d for effect size. Cohen's κ for AI-autonomy inter-rater. Spearman ρ for Load Score vs self-rated stress.

**Data handling.**

- Per-participant aggregated and anonymised before commit.
- Raw CSV (anonymised) published in the public repo at `pilot/analysis/raw_<phase>.csv` for Phase 2 submission.
- No raw personal content (message bodies, names, contact info, full geocoordinates) is committed.
- Audit log Merkle roots from each participant's run are committed to demonstrate tamper-evidence.

**Withdrawal.** Participants can withdraw at any time, in which case their data is deleted from the analysis set within 24 hours. Withdrawal does not require justification.

## Consequences

Positive:

- Sample size hits the brief's quantitative band (30–50) and qualitative band (8–10).
- Unpaid run keeps the budget at ₹2,000 total.
- Public raw CSV is the strongest credibility move available to a student team.
- Plain-language consent and explicit on-device-only invariant align the pilot with the privacy promise on slide 9.

Negative / costs:

- Unpaid recruiting will under-fill on first pass; the 50% buffer is mandatory. Risk R9 in `plan.md` §27.
- The team is its own recruiter, developer, and analyst — no independent oversight. The consent form discloses this honestly.
- IRB-style without IRB approval is a defensible posture for a student submission; not defensible for a clinical claim. We make no clinical claim.
- Pilot exclusively on iOS (ADR-0006) limits the population to iPhone owners, biasing the sample. Disclosed in the analysis section.

## Alternatives

- **Paid pilot at ₹100/quant + ₹500/qual (~₹7,000 total).** Rejected: blows budget by 3.5×.
- **n=10 qual only, no quant.** Rejected: misses the brief's quantitative band and gives no satisfaction / WTP / autonomy numbers for slide 9.
- **Run via a formal IRB at Thapar.** Considered: timeline (12 weeks total, IRB review takes ≥4) makes it impractical for Phase 2. Reconsidered if the project moves to a published study.
- **Recruit via paid panel (e.g. Prolific, UserTesting).** Rejected: cost, and the panel skews away from Indian Gen Z college students who are exactly the target.

End of ADR-0010.
