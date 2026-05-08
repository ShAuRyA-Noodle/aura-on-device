# Reddit r/india + r/developersIndia Launch Post

Plain-English narrative. Indian context first. No marketing register,
no banned words, no hype, no emoji. We are two undergrads telling the
story like we would tell it in a hostel room.

---

## Title

We built an on-device assistant for Indian phones — UPI, IRCTC, Zomato, WhatsApp project groups — on a ₹2,000 budget. It's open-source.

---

## Body

Hi r/india / r/developersIndia.

We are Shaurya and Shorya, two undergraduates at Thapar Institute in
Patiala. For the last twelve weeks we have been quietly building a
project called Aura for the Samsung EnnovateX 2026 hackathon, and
today we are putting it out there for everyone to read, install, and
audit. Posting because it is built specifically for Indian phones and
we figured this sub would tell us where it's wrong.

The repo: github.com/ShAuRyA-Noodle/Combobulating

Honest summary in plain English:

Our phones get something like 237 notifications a day. Most of them
do not matter. Hostel WhatsApp groups, society announcements, Zomato
promos, UPI debit alerts, IRCTC PNR statuses, attendance reminders,
society fest spam. We wanted something that watches the noise on the
device and only buzzes us for the four things that actually matter,
and shows its work when it does.

We refused to make another chatbot. We refused to send any of this
to a server we operate. We refused to ship a screen-time tracker. So
what is left is a small layer that runs four specialist agents on
the phone — one for messages and Gmail, one for calendar, one for UPI
and food/IRCTC receipts, one for HRV and sleep — and a tiny
orchestrator on top that picks at most three quiet actions a day.

The Indian-specific parts that took the longest to get right:

- Twelve bank SMS templates on the hot path. HDFC, ICICI, SBI, Axis,
  Kotak, Yes, IndusInd, RBL, IDFC First, Federal, BoB, PNB. The
  parser handles UPI debit, debit card, salary credit, and reversal.
- IRCTC PNR lookup. Reads the PNR out of the confirmation SMS and
  joins it with the calendar event so you get a Leave-By alert.
- Zomato, Swiggy, Blinkit, Amazon receipts from Gmail. Categorised
  without you having to label.
- BMTC commute time. Hostel WhatsApp project group triage.
- A "Spend Mirror" that just reads the receipts you already received,
  not a manual category tagger.

The architecture parts we are proudest of:

- Every action ships a Reasoning Trace. Trigger, signals, candidates,
  ranking, chosen, rationale, confirm-required, outcome. You can read
  it, edit the chosen action, reject the trace, or rewind. We did
  not ship anything autonomous that could not show its work.
- The Silence Budget. A named state variable that caps proactive
  surfaces at three per local day, settable down to zero. Useful taps
  refund a token. It is inside the ranker, not a filter on top.
- The four agents never talk in free-form prose. Every inter-agent
  message is a typed JSON tool call validated against a schema. This
  is our single biggest hallucination defence.
- Memory is a SQLite graph encrypted at rest with the iOS Secure
  Enclave or Android Keystore. One tap to export to JSON, time-range
  delete, panic-wipe gesture, daily Merkle root for audit
  tamper-evidence.

The constraints, said up front:

- Two-person team. No advisors, no faculty mentor, no contractors.
- ₹2,000 total budget. Printing plus buffer. We do not own a flagship
  Galaxy phone. iPhone is the reference build. Galaxy ecosystem is
  the production target. Slide 4a in the deck maps every iOS API
  one-for-one to its Android counterpart so we are not pretending.
- No paid Apple Developer Program. We use a free Apple ID Personal
  Team certificate, which means a seven-day install that you re-flash
  whenever you plug your iPhone back in. The site has the step-by-step
  for evaluators.
- Twelve-week runway. Phase 1 blueprint (deck, threat model, ADRs).
  Phase 2 pilot (30 quantitative users, 8 qualitative interviews,
  raw CSV in the repo). Phase 3 finals demo at Bangalore.

What is in the repo right now:

- Eleven Architecture Decision Records under `docs/decisions/`.
- A threat model under `docs/threat_model.md` with five named
  adversaries — curious app, lost device, malicious notification
  listener, OS account compromise, parental coercion — and concrete
  mitigations for each. Panic-wipe gesture spec included.
- The orchestrator (Phi-3-mini Q4 on a seven-state LangGraph machine).
- Four agent reference implementations.
- The memory graph schema, migrations, audit log.
- The Wizard-of-Oz pilot kit — consent forms, qualitative and
  quantitative protocols, recruitment poster, raw-data templates.
- A live Gradio demo on HuggingFace —
  huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin — synthetic data
  only, no PII, free CPU tier.
- A site at shaurya-noodle.github.io/Combobulating with install
  instructions for sideloading on a personal iPhone.

What we want from this sub:

1. Tell us what we got wrong about the Indian context. We are at
   Thapar; if you are in Bangalore, Mumbai, Delhi, Chennai, Kolkata,
   Pune, or anywhere we are not, your edge cases are different from
   ours and we want to hear them.
2. If you are in Bangalore or Patiala and you would like to be in
   the qualitative pilot cohort, ping us. The interview is sixty
   minutes plus a daily diary.
3. If you have built on-device ML on Indian phones — particularly
   anything around UPI parsing, regional language SMS, or Health
   Connect — we would love to compare notes.

MIT licensed. No funding round behind us. Just two undergrads with
an Alienware laptop and a hostel room.

Thanks for reading.

— Shaurya Punj, Shorya Gupta.
   spunj_be23@thapar.edu, sgupta9_be24@thapar.edu.
   Galaxy Brain. Thapar Institute, Patiala.
