<div align="center">

# Aura

**Anticipate. Act. Stay quiet.**

An on-device empathetic intelligence layer for Indian Gen Z and Gen Alpha. Four specialist agents, one Phi-3-mini orchestrator, a glass-box Reasoning Trace, and a memory graph the user owns.

[![build](https://img.shields.io/github/actions/workflow/status/ShAuRyA-Noodle/Combobulating/ci.yml?branch=main&label=build)](https://github.com/ShAuRyA-Noodle/Combobulating/actions)
[![hf space](https://img.shields.io/badge/%F0%9F%A4%97%20space-Caramel__Coin-FF5B2E)](https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin)
[![pages](https://img.shields.io/github/deployments/ShAuRyA-Noodle/Combobulating/github-pages?label=pages)](https://shaurya-noodle.github.io/Combobulating/)
[![license](https://img.shields.io/github/license/ShAuRyA-Noodle/Combobulating)](LICENSE)
[![last commit](https://img.shields.io/github/last-commit/ShAuRyA-Noodle/Combobulating)](https://github.com/ShAuRyA-Noodle/Combobulating/commits/main)
[![contributors](https://img.shields.io/github/contributors/ShAuRyA-Noodle/Combobulating)](https://github.com/ShAuRyA-Noodle/Combobulating/graphs/contributors)
[![release](https://img.shields.io/github/v/release/ShAuRyA-Noodle/Combobulating?include_prereleases)](https://github.com/ShAuRyA-Noodle/Combobulating/releases)

</div>

---

Aura is a continuous, on-device orchestrator that watches the signals already on a Gen Z phone — notifications, calendar events, UPI SMS, Gmail receipts, HRV, sleep — and turns the four that matter into one quiet action a few times a day. Nothing leaves the device unless the user presses export. Every action ships with a Reasoning Trace the user can read, edit, or reject. Built by Galaxy Brain at Thapar Institute for Samsung EnnovateX 2026, on a total budget of two thousand rupees.

## Why Aura

The average Gen Z phone receives 237 notifications a day. Four of them matter. The other 233 are a tax on attention that nobody chose to pay. Existing assistants — Gemini Live, Apple Intelligence, Bixby, Pixel Assistant, Rabbit, Humane — start when the user starts. None of them see HRV, none read the WhatsApp project group, none parse a UPI SMS, and none expose a step-by-step trace the user can audit. Aura closes that loop on the device, with five defended product wedges shipped together.

## The five wedges

<table>
<tr>
<td width="50%">

**1. Indian context, not bolt-on**

UPI parser, IRCTC PNR lookup, Zomato and Swiggy receipt extraction, Blinkit delivery windows, BMTC commute, Gmail thread reconciliation. Twelve bank SMS templates on the hot path.

![Spend Mirror](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_05_screen_spend_mirror.png)

</td>
<td width="50%">

**2. Closed biometric loop**

HRV from HealthKit or Health Connect feeds an XGBoost Load Score that triggers a single quiet intervention — mute, breathe, nap.

![Load Score](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_07_screen_load_score_panel.png)

</td>
</tr>
<tr>
<td width="50%">

**3. Glass-box Reasoning Trace**

Every action emits trigger, signals, candidates, ranking, chosen, rationale, and outcome. Inspect, edit, reject, or rewind any decision.

![Reasoning Trace](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_03_screen_reasoning_trace_drawer.png)

</td>
<td width="50%">

**4. Silence as a feature**

A daily Silence Budget caps proactive surfaces at three. Useful taps refund a token. The cap is a hard floor on a learned cost function, not the function itself.

![Silence Budget](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_08_screen_silence_budget_state.png)

</td>
</tr>
<tr>
<td colspan="2">

**5. Owned memory graph**

SQLite plus sqlite-vss, encrypted at rest with Secure Enclave or Keystore. Nine node types, eight edge types, one-tap export, time-range delete, panic-wipe gesture, daily Merkle root for audit.

![Memory Tab](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_04_screen_memory_tab.png)

</td>
</tr>
</table>

## Architecture

Three layers. Four agents. One orchestrator.

![Three-layer architecture](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_12_arch_3_layer_diagram.png)

- **Sense.** Reads on-device signals only. iOS: HealthKit, EventKit, App Intents, Background Tasks. Android: UsageStatsManager, NotificationListenerService, Health Connect, Calendar Provider, custom IME for typing-entropy buckets (entropy only, never characters).
- **Intelligence.** Four agents and one Phi-3-mini orchestrator. CommsAgent and FinanceAgent run Gemma 2B Q4 with LoRA adapters. CalendarAgent runs a rule engine plus Phi-3-mini for prose. WellnessAgent runs an XGBoost Load Score plus Phi-3-mini. The orchestrator is a deterministic LangGraph state machine across seven named states with typed JSON tool calls.
- **Experience.** Phone, watch, earbuds, tablet. Morning Brief card, action card, Reasoning Trace drawer, Memory tab, Spend Mirror, Quiet Group Chat. Cross-surface continuity via Multipeer Connectivity on iOS and Nearby Connections on Android.

Full document at [`docs/architecture.md`](docs/architecture.md). Eleven Architecture Decision Records under [`docs/decisions/`](docs/decisions/).

## Get the demo

A Gradio Space runs a synthetic-data showcase of the orchestrator and Reasoning Trace on the free CPU tier — no PII, no install. Try it here.

[**Caramel_Coin on HuggingFace Spaces**](https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin)

For the iPhone build, see [`docs/site/install.html`](docs/site/install.html). The Apple Personal Team certificate from a free Apple ID signs and sideloads the app onto a personal iPhone for seven days at a time. No paid Apple Developer Program needed for evaluators.

## Get the source

```bash
git clone https://github.com/ShAuRyA-Noodle/Combobulating.git
cd Combobulating/aura

# Python orchestrator + agents
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Run the orchestrator state machine
python -m orchestrator --help

# Run the test suite
pytest

# iOS reference build
cd apps/ios/Aura
brew install xcodegen
xcodegen generate
open Aura.xcodeproj
```

## Pilot study

A Wizard-of-Oz pilot at Thapar campus, designed for Phase 2.

- **Quantitative.** 30 users across years and branches. Five standardised tasks, randomised order, baseline measured first. Stopwatch, tap count, in-app telemetry. Means with 95% confidence intervals, paired Wilcoxon, Cohen's d.
- **Qualitative.** 8 users, 60-minute semi-structured interviews, daily diary entries.
- **Wizard-of-Oz.** A human operator drives the orchestrator while the user sees only the action card and Reasoning Trace. Operator latency budget 2.5 s p95. Operator script and consent form under [`pilot/`](pilot/).
- **Six KPIs** match the EnnovateX brief one-for-one. Effort reduction ≥ 30 %, task completion ≥ 90 %, autonomy quality ≥ 85 %, satisfaction ≥ 4.5 / 5, HRV trend up, willingness to pay ₹199 / month ≥ 60 % via Van Westendorp.

Raw CSV publishes in the repo with the Phase 2 cut.

## Privacy — zero-cloud promise

1. Your data lives on your device.
2. Nothing leaves the device unless you press export.
3. Every action shows its work, and you can erase the work.
4. Aura speaks at most three times a day, and you can take that to zero.
5. Five rapid taps wipe everything, including from us.

Each promise is tested against the [threat model](docs/threat_model.md). Five named adversaries, STRIDE per surface, panic-wipe spec at [`docs/threat_model.md`](docs/threat_model.md). Full text at [`docs/privacy_promises.md`](docs/privacy_promises.md).

## Team Galaxy Brain

Two undergraduates at Thapar Institute of Engineering and Technology, Patiala. We are the user we design for.

![Team Galaxy Brain](https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_22_press_kit_team_portrait.png)

- **Shaurya Punj** — third-year ECE. Architecture, Wellness agent, KPI study, pitch. Roll 102486013. spunj_be23@thapar.edu.
- **Shorya Gupta** — second-year Computer Engineering. iOS app, Comms / Calendar / Finance agents, memory graph, audit log. Roll 1024037521. sgupta9_be24@thapar.edu.

## License

MIT. See [`LICENSE`](LICENSE).

## Citation

```bibtex
@software{galaxy_brain_aura_2026,
  author       = {Punj, Shaurya and Gupta, Shorya},
  title        = {Aura: An On-Device Empathetic Intelligence Layer for Indian Gen Z},
  year         = {2026},
  version      = {1.0.0},
  publisher    = {Galaxy Brain, Thapar Institute of Engineering and Technology},
  url          = {https://github.com/ShAuRyA-Noodle/Combobulating},
  note         = {Samsung EnnovateX 2026}
}
```

A machine-readable [`CITATION.cff`](CITATION.cff) is also provided.
