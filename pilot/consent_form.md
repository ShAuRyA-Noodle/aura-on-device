# Aura Pilot — Participant Consent Form

Project: **Aura** (team Galaxy Brain, Thapar Institute of Engineering and Technology)
Study type: Unpaid academic research, not commercial
Pilot platform: iPhone via TestFlight
Last updated: 2026-05-07

---

## 1. What this is, in plain English

Hi. We are Shaurya and Shorya, two students at Thapar building an experimental phone assistant called Aura. Aura watches a few signals on your phone and tries to do small useful things — quiet a noisy WhatsApp group at the right moment, summarise your morning, flag a UPI debit that looks unusual, or suggest a breathing pause when your watch shows your heart-rate variability has dropped.

We are running a 7-day pilot to see if Aura actually helps. We need 30 people for short task-and-survey sessions and 8 people for longer interviews. Everyone in the pilot is a friend or classmate — there is no payment, no Amazon voucher, no perk. You are helping us because you are kind and curious. That is the whole exchange.

This document tells you exactly what Aura sees, where the data lives, and what your rights are. Read it slowly. If anything sounds off, tell us and we will fix it before you start.

---

## 2. What Aura reads from your phone

Aura needs read access to a few specific data sources to do its job. Each one is opt-in via a separate checkbox below. You can decline any one of them and still be in the study.

| Source | What we read | Why we need it |
|---|---|---|
| **HealthKit** | Heart rate, heart-rate variability (HRV), sleep, step count | To compute a daily Load Score and notice when you are stressed |
| **EventKit** (calendar) | Event titles, times, locations on your phone calendar | To produce the morning brief and detect conflicts |
| **Gmail metadata** (read-only) | Sender, subject, timestamp, label of incoming email — **not message body except receipt parsing for known senders like Zomato, Swiggy, Blinkit, IRCTC, Amazon** | To triage email and parse spend |
| **Notification listener** (own-app channel) | Sender app, sender name hash, timestamp, urgency score on notifications routed through the Aura test channel | To learn what to surface and what to suppress |
| **Voice prosody** (optional) | One-second audio energy windows for stress prosody — **no transcript ever** | To improve stress detection. Decline freely; the model works without this. |

Aura does **not** read:
- WhatsApp message bodies (iOS does not allow this anyway)
- SMS content (iOS does not allow this anyway)
- Any photo, file, or document
- Your location beyond a 200-metre grid bucket
- Any data from any app you have not approved

---

## 3. Where the data lives

- **All data stays on your iPhone.** Nothing is uploaded to our servers. We do not run servers.
- The on-device store is encrypted at rest using the iOS Secure Enclave. If your phone is locked, the data is not readable.
- The Aura app cannot send your data anywhere unless you explicitly tap "Export" or "Share with researchers".
- For the pilot, we will collect three things from you only:
  1. **Anonymised CSV logs** of your task sessions (taps, times, success flags) — exported by you, attached to a Google Form by you, after you have reviewed them.
  2. **Survey answers** you fill in on Google Forms.
  3. **Interview audio** (only for the 8 qualitative participants) — recorded on a separate device, with your consent, transcribed by us, deleted after coding.
- We will never read your raw phone data. The only things that leave your phone are the aggregated CSVs you choose to share.

---

## 4. Your rights, all of them

You can do any of the following at any time, without giving a reason:

- **Pause Aura.** Open Settings → Aura → Pause. Aura stops reading and writing.
- **Export everything Aura has on you.** One tap. JSON file in your Files app.
- **Delete by category.** One tap to delete all health data, all calendar data, all email data, etc.
- **Delete by time-range.** Pick a date range, delete everything Aura captured in that window.
- **Delete everything.** One tap. Aura is gone, OAuth tokens revoked.
- **View the audit log.** Every read and write Aura made on your phone is logged with a tamper-evident daily Merkle root. You can see it whenever you want.
- **Withdraw from the study.** Email us at workwithshaurya10@gmail.com or message Shaurya on WhatsApp. We will delete every artefact you sent us within 7 days and confirm in writing. No questions.

You do not need to finish the 7 days. Quitting partway is fine and does not affect the friendship.

---

## 5. Risks, honestly

- Battery drain: ~6–8% extra per day during the pilot, mostly from the on-device LLM running.
- Storage: ~3 GB of model files on your phone.
- A small chance of a bug surfacing a notification at a bad time. We have a 3-per-day hard cap to limit this.
- A small chance that the on-device model misclassifies a message. You can always reject the action — nothing happens without your tap.
- Embarrassment: you may see what Aura inferred about you (e.g. "you look stressed"). You can hide or delete this any time.

There is **no risk of your data being seen by anyone outside your phone** unless you explicitly export and share it.

---

## 6. What we will do with the results

- Aggregate, anonymised numbers (means, percentages, charts) will appear in our Phase 2 submission to Samsung EnnovateX 2026.
- Anonymised raw CSVs may be published in our public GitHub repo so judges can verify our claims. Your participant ID is `P001`–`P030`; no name, phone number, or email is in the CSV.
- Anonymised quotes from interviews may appear in the report, with names changed and any identifying detail removed. You will see and approve any quote attributed to you before it is published.

---

## 7. Not commercial. Not paid.

This is academic coursework done as a hackathon entry. We are not a company. We are not paid for this. You are not paid for this. There is no incentive offered or implied. Aura may or may not become a real product later. If it does, your pilot data does not transfer to a future commercial entity without a separate, fresh consent.

---

## 8. Who to contact

- Shaurya Punj — workwithshaurya10@gmail.com — WhatsApp via Thapar contacts
- Shorya Gupta — Thapar contacts

If you would prefer to talk to a faculty member instead of us, email any Thapar ECE / CSE faculty and they can mediate.

---

## 9. Checkboxes — please tick what you agree to

Tick every box that applies. Leaving a box unticked is a No, and we respect that completely.

- [ ] I have read this document. I understand what Aura reads, where the data lives, and what my rights are.
- [ ] I consent to Aura reading my **HealthKit** data (HR, HRV, sleep, steps).
- [ ] I consent to Aura reading my **EventKit** (calendar) data.
- [ ] I consent to Aura reading my **Gmail metadata** (sender, subject, timestamp) and **parsing receipts** from named senders only.
- [ ] I consent to Aura listening on its **notification channel** for routed notifications.
- [ ] *(Optional)* I consent to Aura recording **voice prosody features** in 1-second energy windows. No transcript will ever be stored.
- [ ] I consent to filling **daily diary prompts** (3 questions, ~90 seconds) for 7 days.
- [ ] I consent to completing the **post-trial Google Form survey** (~12 minutes).
- [ ] *(Qualitative participants only)* I consent to a **60-minute audio-recorded interview**. The audio will be deleted after coding.
- [ ] I understand this is **unpaid academic research** with no incentive.
- [ ] I understand I can **withdraw at any time** without giving a reason.
- [ ] I understand my data **stays on my phone** and only the artefacts I explicitly export will be shared.

---

## 10. Signatures

| | Name (printed) | Signature | Date |
|---|---|---|---|
| Participant | ________________________ | ________________________ | __ / __ / 2026 |
| Researcher (Shaurya / Shorya) | ________________________ | ________________________ | __ / __ / 2026 |

Two copies. One stays with you. One stays in our locked folder on the Alienware, never on cloud.

---

End of consent form.
