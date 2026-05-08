# X / Twitter Launch Thread — Aura v1.0.0

Twelve tweets. First tweet ≤ 280 characters. Each subsequent tweet
specific, not hyped, no banned words, no emoji, no exclamation marks.

Char counts noted at the end of each tweet, with spaces.

---

## 1 / 12

Aura is live.

An on-device empathetic intelligence layer for Indian Gen Z. Four
agents, one Phi-3-mini orchestrator, a glass-box Reasoning Trace, a
Silence Budget capped at 3/day.

Built by two undergrads at Thapar on a ₹2,000 budget.

github.com/ShAuRyA-Noodle/Combobulating

(279 chars)

---

## 2 / 12

The friction Aura answers: 237 notifications a day on a Gen Z phone
(Common Sense Media, 2023). Four matter. The other 233 are a tax on
attention nobody chose to pay.

We do not optimise screen time. We surface the four and let the rest
stay quiet.

(244 chars)

---

## 3 / 12

Four on-device agents:

- CommsAgent: WhatsApp groups, Gmail, notifications
- CalendarAgent: Google + EventKit + travel time
- FinanceAgent: UPI SMS, Zomato, Swiggy, Blinkit, IRCTC
- WellnessAgent: HRV, sleep, Load Score

Typed JSON between them. Never free-form chat.

(252 chars)

---

## 4 / 12

The orchestrator is Phi-3-mini Q4 on a deterministic LangGraph state
machine across seven states. Cooldown state with a hard timeout. Ranking
policy is utility minus notification cost minus recent-action penalty.

The cap of 3/day is a hard floor on that cost function.

(263 chars)

---

## 5 / 12

Every action ships a Reasoning Trace.

Trigger. Signals. Candidates. Ranking. Chosen. Rationale.
Confirm-required. Outcome.

You can read it, edit the chosen action, reject the trace, or rewind.
We do not believe in black boxes for an autonomous layer on a personal
phone.

(259 chars)

---

## 6 / 12

Memory is a SQLite graph with sqlite-vss for embeddings, encrypted at
rest with the iOS Secure Enclave or Android Keystore. Nine node types,
eight edge types.

One tap to export. Time-range delete. Daily Merkle root in Settings so
you can verify the audit log hasn't been edited.

(279 chars)

---

## 7 / 12

Five privacy promises:

1. Your data lives on your device.
2. Nothing leaves unless you press export.
3. Every action shows its work, and you can erase the work.
4. Aura speaks ≤ 3 times a day, settable to zero.
5. Five rapid taps wipe everything, including from us.

(262 chars)

---

## 8 / 12

The Indian context wedge is not a sticker. Twelve bank SMS templates on
the hot path. UPI debit parser. IRCTC PNR lookup. Zomato, Swiggy,
Blinkit, Amazon receipt extraction from Gmail. Hostel WhatsApp project
group triage.

We are the user we design for.

(248 chars)

---

## 9 / 12

The constraint, said up front:

- Apple-only Phase 1 + 2 reference build
- Galaxy ecosystem is the production target
- ₹2,000 total budget
- Two-person team, no advisors
- 12-week runway

We frame it. We do not apologise for it.

(225 chars)

---

## 10 / 12

Try it without installing:

A Gradio Space — Caramel_Coin — runs a synthetic-data showcase of the
orchestrator and Reasoning Trace on the free CPU tier. No PII.

huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin

(213 chars)

---

## 11 / 12

For the iPhone build, sideload with a free Apple ID Personal Team
certificate. Seven-day install, repeats indefinitely. Full step-by-step
on the site:

shaurya-noodle.github.io/Combobulating/install.html

No paid Apple Developer Program needed for evaluators or pilot users.

(269 chars)

---

## 12 / 12

Galaxy Brain — Shaurya Punj, Shorya Gupta. Thapar, Patiala.
EnnovateX 2026.

Repo: github.com/ShAuRyA-Noodle/Combobulating
Demo: hf.co/spaces/Shaurya-Noodle/Caramel_Coin
Site: shaurya-noodle.github.io/Combobulating

MIT. v1.0.0.

(238 chars)
