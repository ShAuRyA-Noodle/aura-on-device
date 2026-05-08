# Aura — Fact Sheet

Single-page, A4-ready. Galaxy Brain — Shaurya Punj, Shorya Gupta —
Thapar Institute of Engineering and Technology, Patiala.
Samsung EnnovateX 2026. v1.0.0, dated 2026-05-07.

---

## In one sentence

Aura is an on-device, multi-agent empathetic intelligence layer
for Indian Gen Z that anticipates, acts, and stays quiet.

---

## Five numbers

| # | Value | What it measures |
|---|---|---|
| 1 | **237** | Notifications a day on a Gen Z phone (Common Sense Media, 2023). |
| 2 | **3 / day** | Hard cap on proactive non-safety surfaces. Settable to zero. |
| 3 | **₹2,000** | Total project budget. Printing plus buffer. |
| 4 | **2** | People on the team. No advisors. |
| 5 | **11** | Architecture Decision Records that govern every product choice. |

---

## Five product wedges

1. **Indian context, not bolt-on.** UPI, IRCTC, Zomato, Swiggy, Blinkit, BMTC, Gmail. Twelve bank SMS templates on the hot path.
2. **Closed biometric loop.** HRV via HealthKit or Health Connect drives an XGBoost Load Score that triggers one quiet intervention.
3. **Glass-box Reasoning Trace.** Every action ships trigger, signals, candidates, ranking, chosen, rationale, confirm-required, outcome.
4. **Silence as a feature.** A daily Silence Budget — a named state variable inside the orchestrator's ranker, not a filter on top.
5. **Owned memory graph.** SQLite + sqlite-vss, encrypted at rest. One-tap export, time-range delete, panic-wipe gesture, daily Merkle root.

---

## Architecture, in one line

Three layers — Sense, Intelligence, Experience. Four specialist agents (Comms, Calendar, Finance, Wellness) coordinated by a Phi-3-mini Q4 orchestrator on a deterministic seven-state LangGraph state machine, with typed JSON tool calls and a SQLCipher memory graph on-device.

---

## The team

**Shaurya Punj.** Co-founder, systems. Third-year Electronics and Communication Engineering at Thapar. Owns architecture, the Wellness agent, the KPI study, pitch delivery. Roll 102486013. spunj_be23@thapar.edu. GitHub ShAuRyA-Noodle.

**Shorya Gupta.** Co-founder, build. Second-year Computer Engineering at Thapar. Owns the iOS app, the Comms / Calendar / Finance agents, the memory graph and audit log. Roll 1024037521. sgupta9_be24@thapar.edu.

---

## Links

- Repository — github.com/ShAuRyA-Noodle/Combobulating
- Live demo — huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin
- Site — shaurya-noodle.github.io/Combobulating
- Install guide — shaurya-noodle.github.io/Combobulating/install.html
- Press kit — `press_kit/` in the repo, or run `bash press_kit/build_press_kit.sh`
- Security disclosure — `/.well-known/security.txt`
- Citation — `CITATION.cff` in the repo

---

## License

MIT. Use, modify, redistribute. Cite us if you publish on top of it.
