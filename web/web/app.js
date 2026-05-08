/* Aura — local stage frontend.
 *
 * Single-file React component tree with no build step. Uses `htm` (Hyperscript
 * Tagged Markup) so we can write JSX-ish syntax in plain JS — keeps the bundle
 * vendorable and CDN-free at the venue.
 *
 * Talks to the local FastAPI on :8000. Falls back to an in-page warning if the
 * API isn't up (e.g., the operator only opened index.html with no server).
 */

(function () {
  "use strict";

  const html = window.htm.bind(React.createElement);
  const { useState, useEffect, useCallback, useRef } = React;

  // Pick up ?api= and ?token= query string injected by run_local.sh so the
  // browser inherits the same per-session token the iOS app reads from the
  // QR code. Falls back to localhost:8000 with no token (dev mode).
  const _qs = new URLSearchParams(window.location.search);
  const API_BASE = _qs.get("api") || window.AURA_API_BASE || "http://localhost:8000";
  const AUTH_TOKEN = _qs.get("token") || window.AURA_TOKEN || "";
  const API = API_BASE + "/api";
  const WS_TRACE = (
    API_BASE.replace(/^http/, "ws") +
    "/ws/trace" +
    (AUTH_TOKEN ? "?token=" + encodeURIComponent(AUTH_TOKEN) : "")
  );

  // ---------------------------------------------------------------------
  // Synthetic fixtures (mirror the Gradio Space's defaults).
  // ---------------------------------------------------------------------

  const EXAMPLE_GROUP_CHAT = [
    "[09:01] @aarav: gn folks",
    "[09:02] @rhea: lol same",
    "[09:03] @sid: btw quiz tomorrow @you can you share notes",
    "[09:05] @pri: thx aarav",
    "[09:06] @aarav: brb",
    "[09:07] @sid: @you reminder — viva at 4pm today, please confirm",
    "[09:23] @sid: please submit lab report by tonight",
    "[09:30] @rhea: btw Prof shared deadline asap urgent",
    "[09:33] @sid: @you can you push the merge before 5",
    "[09:56] @aarav: confirm the meeting at 5",
    "[10:00] @sid: please reply on the rebase pr",
    "[10:03] @ish: nice",
  ].join("\n");

  const EXAMPLE_SMS = [
    "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY",
    "INR 250.00 spent on ICICI Bank Card XX9921 at SWIGGY on 07-May-26",
    "INR 540 debited A/c no. XX2245 07-05-26 13:42 UPI/P2A/uber@axis/Uber",
    "Dear Customer, Rs.1200.00 debited from A/c X3389 on 07-05-26 to VPA bigbasket@okhdfc Ref 412345. -SBI",
  ].join("\n");

  // ---------------------------------------------------------------------
  // Generic helpers
  // ---------------------------------------------------------------------

  function pillTone(score) {
    if (score >= 70) return "high";
    if (score >= 50) return "mid";
    return "low";
  }

  function _authHeaders() {
    const h = { "Content-Type": "application/json" };
    if (AUTH_TOKEN) h.Authorization = "Bearer " + AUTH_TOKEN;
    return h;
  }

  async function postJSON(path, body) {
    const res = await fetch(API + path, {
      method: "POST",
      headers: _authHeaders(),
      body: JSON.stringify(body || {}),
    });
    if (!res.ok) throw new Error("HTTP " + res.status + " " + res.statusText);
    return res.json();
  }

  async function ping() {
    try {
      // /health is on the root, not /api.
      const res = await fetch(API_BASE + "/health");
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  // ---------------------------------------------------------------------
  // Live trace overlay — subscribes to /ws/trace and renders the last
  // 12 events. During a live demo the team can flip from the iPhone to
  // the laptop browser and see the same Reasoning Trace stream.
  // ---------------------------------------------------------------------

  function TraceOverlay() {
    const [events, setEvents] = useState([]);
    const [status, setStatus] = useState("connecting");
    const wsRef = useRef(null);

    useEffect(() => {
      let cancelled = false;
      let retryTimer = null;
      function connect() {
        try {
          const ws = new WebSocket(WS_TRACE);
          wsRef.current = ws;
          ws.onopen = () => !cancelled && setStatus("live");
          ws.onmessage = (msg) => {
            if (cancelled) return;
            try {
              const evt = JSON.parse(msg.data);
              if (evt.type === "heartbeat") return;
              setEvents((prev) => prev.concat([evt]).slice(-12));
            } catch (_) { /* ignore */ }
          };
          ws.onerror = () => !cancelled && setStatus("error");
          ws.onclose = () => {
            if (cancelled) return;
            setStatus("retry");
            retryTimer = setTimeout(connect, 2000);
          };
        } catch (_) {
          setStatus("error");
        }
      }
      connect();
      return () => {
        cancelled = true;
        if (retryTimer) clearTimeout(retryTimer);
        if (wsRef.current) try { wsRef.current.close(); } catch (_) { /* */ }
      };
    }, []);

    return html`
      <aside class="trace-overlay" data-status=${status}>
        <header>
          <strong>Reasoning Trace</strong>
          <span class="status-pill ${status}">${status}</span>
        </header>
        <ol class="trace-list">
          ${events.length === 0
            ? html`<li class="muted">Waiting for the next tick…</li>`
            : events.map((e, i) => html`
                <li key=${i}>
                  <span class="evt-type">${e.type || "?"}</span>
                  <span class="evt-detail">
                    ${e.type === "trace.emitted"
                      ? (e.trace && e.trace.chosen) || ""
                      : e.type === "agent.output"
                        ? (e.agent || "")
                        : e.type === "policy.decision"
                          ? (e.chosen_kind || "")
                          : ""}
                  </span>
                </li>`)}
        </ol>
      </aside>
    `;
  }

  // ---------------------------------------------------------------------
  // Hero banner
  // ---------------------------------------------------------------------

  function Hero() {
    return html`
      <header class="aura-hero">
        <div class="aura-hero-row">
          <svg width="44" height="44" viewBox="0 0 44 44" aria-hidden="true">
            <circle cx="22" cy="22" r="20" fill="none" stroke="#0E0E0E" stroke-width="2" />
            <circle cx="22" cy="22" r="6" fill="#FF5B2E" />
          </svg>
          <div>
            <h1>Aura</h1>
            <p class="tag">Anticipate. Act. Stay quiet.</p>
          </div>
        </div>
        <div class="aura-disclaimer">
          DEMO ON SYNTHETIC DATA — NO USER DATA EVER LEAVES YOUR DEVICE IN PRODUCTION
        </div>
      </header>
    `;
  }

  // ---------------------------------------------------------------------
  // Tab 1 — Morning Brief / Orchestrator replay
  // ---------------------------------------------------------------------

  function MorningBrief() {
    const [rmssd, setRmssd] = useState(45);
    const [sleep, setSleep] = useState(60);
    const [notif, setNotif] = useState(12);
    const [conflict, setConflict] = useState(false);
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(false);

    const run = useCallback(async () => {
      setLoading(true); setErr(null);
      try {
        // Build canned synthetic events.
        const seed = [
          { id: "n_001", app_pkg: "wa", channel: "ch_friends", preview: "lol same",
            intent_hint: "social", ts: "2026-05-07T08:30:00+00:00" },
          { id: "n_002", app_pkg: "wa", channel: "ch_class",
            preview: "@you reminder viva at 4pm please confirm",
            intent_hint: "actionable", ts: "2026-05-07T08:30:00+00:00" },
          { id: "n_003", app_pkg: "slack", channel: "ch_team",
            preview: "please push the merge before 5",
            intent_hint: "actionable", ts: "2026-05-07T08:30:00+00:00" },
        ];
        const notif_events = [];
        for (let i = 0; i < notif; i++) {
          const s = seed[i % seed.length];
          notif_events.push(Object.assign({}, s, { id: `n_${String(i).padStart(3, "0")}` }));
        }
        const events = [
          { id: "ev_morning", title: "Standup",
            start: "2026-05-07T09:00:00+00:00", end: "2026-05-07T09:30:00+00:00" },
          { id: "ev_class", title: "DSA class",
            start: "2026-05-07T10:00:00+00:00", end: "2026-05-07T11:00:00+00:00" },
        ];
        if (conflict) events.push({
          id: "ev_lab", title: "Lab review",
          start: "2026-05-07T10:30:00+00:00", end: "2026-05-07T11:30:00+00:00",
        });
        const body = {
          tick_ts: "2026-05-07T08:30:00+00:00",
          comms: { notif_events, gmail_threads: [] },
          calendar: { events_today: events, buffer_minutes: 15 },
          finance: { sms: [] },
          wellness: {
            rmssd_ms: rmssd, typing_entropy: 4.2, app_switch_rate: 8,
            sleep_debt_min: sleep, notif_dismiss_rate: 0.4, screen_on_min: 30,
          },
        };
        setData(await postJSON("/orchestrator/run_replay", body));
      } catch (e) { setErr(String(e)); }
      finally { setLoading(false); }
    }, [rmssd, sleep, notif, conflict]);

    const wellness = data && data.agent_outputs.find(o => o.agent === "wellness");
    const comms = data && data.agent_outputs.find(o => o.agent === "comms");
    const cal = data && data.agent_outputs.find(o => o.agent === "calendar");
    const score = wellness ? (wellness.payload.load_score || 0) : 0;
    const interv = wellness ? (wellness.payload.suggested_intervention || {}) : {};

    return html`
      <section>
        <h2>Morning Brief</h2>
        <p class="muted">Synthetic Health + Calendar + Comms inputs flow through the orchestrator.</p>

        <div class="slider-row">
          <label>Resting RMSSD (ms)</label>
          <input type="range" min="15" max="80" value=${rmssd}
                 oninput=${e => setRmssd(Number(e.target.value))} />
          <span class="slider-val">${rmssd}</span>
        </div>
        <div class="slider-row">
          <label>Sleep debt (min)</label>
          <input type="range" min="0" max="240" step="5" value=${sleep}
                 oninput=${e => setSleep(Number(e.target.value))} />
          <span class="slider-val">${sleep}</span>
        </div>
        <div class="slider-row">
          <label>Notification volume</label>
          <input type="range" min="0" max="60" value=${notif}
                 oninput=${e => setNotif(Number(e.target.value))} />
          <span class="slider-val">${notif}</span>
        </div>
        <label class="field">
          <input type="checkbox" checked=${conflict} onchange=${e => setConflict(e.target.checked)} />
          ${" "}Calendar conflict
        </label>

        <button class="primary" onclick=${run} disabled=${loading}>
          ${loading ? "Running…" : "Run morning brief"}
        </button>

        ${err && html`<div class="status-banner error">${err}</div>`}

        ${data && html`
          <div class="aura-card">
            <div class="card-head">
              <span class="eyebrow">Morning brief</span>
              <span class="pill ${pillTone(score)}">${data.chosen_kind}</span>
            </div>
            <div class="grid-2">
              <div class="row"><span class="label">Load score</span><span class="value">${score}</span></div>
              <div class="row"><span class="label">Intervention</span><span class="value">${interv.kind || "DO_NOTHING"}</span></div>
              <div class="row"><span class="label">Actionable</span><span class="value">${comms ? (comms.payload.urgent || []).length : 0}</span></div>
              <div class="row"><span class="label">Muted</span><span class="value">${comms ? (comms.payload.muted_count || 0) : 0}</span></div>
              <div class="row"><span class="label">Conflicts</span><span class="value">${cal ? (cal.payload.conflicts || []).length : 0}</span></div>
              <div class="row"><span class="label">Cap reason</span><span class="value">${data.cap_reason || "—"}</span></div>
            </div>
            <p class="rationale">${(data.trace && data.trace.rationale) || ""}</p>
          </div>
          <pre class="code">${JSON.stringify(data.trace, null, 2)}</pre>
        `}
      </section>
    `;
  }

  // ---------------------------------------------------------------------
  // Tab 2 — Quiet Group Chat
  // ---------------------------------------------------------------------

  function QuietGroup() {
    const [text, setText] = useState(EXAMPLE_GROUP_CHAT);
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(false);

    const run = useCallback(async () => {
      setLoading(true); setErr(null);
      try {
        const lines = text.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
        const notif_events = lines.slice(0, 80).map((l, i) => ({
          id: `n_${String(i).padStart(3, "0")}`,
          app_pkg: "wa", channel: "ch_demo",
          preview: l, intent_hint: l.slice(0, 40),
          ts: "2026-05-07T09:00:00+00:00",
        }));
        setData(await postJSON("/comms/triage", {
          notif_events, gmail_threads: [], load_score: 72,
          tick_ts: "2026-05-07T09:00:00+00:00",
        }));
      } catch (e) { setErr(String(e)); }
      finally { setLoading(false); }
    }, [text]);

    return html`
      <section>
        <h2>Quiet Group Chat</h2>
        <p class="muted">Paste any chat blob. CommsAgent triages to actionable + muted.</p>

        <label class="field">Group chat (any format)</label>
        <textarea rows="14" value=${text} oninput=${e => setText(e.target.value)}></textarea>

        <button class="primary" onclick=${run} disabled=${loading}>
          ${loading ? "Triaging…" : "Triage"}
        </button>
        ${err && html`<div class="status-banner error">${err}</div>`}

        ${data && html`
          <div class="aura-card">
            <div class="card-head">
              <span class="eyebrow">Triage result</span>
              <span class="pill">${data.payload.top_suggested_action}</span>
            </div>
            <div class="grid-2">
              <div class="row"><span class="label">Total</span><span class="value">${(data.payload.urgent || []).length + (data.payload.muted_count || 0)}</span></div>
              <div class="row"><span class="label">Actionable</span><span class="value">${(data.payload.urgent || []).length}</span></div>
              <div class="row"><span class="label">Muted</span><span class="value">${data.payload.muted_count || 0}</span></div>
              <div class="row"><span class="label">Drafts</span><span class="value">${(data.payload.drafts || []).length}</span></div>
            </div>
            <ul class="bare">
              ${(data.payload.urgent || []).map(u => html`
                <li><span><code>${u.item_id}</code> · ${u.reason_code}</span><span>${(u.score || 0).toFixed(2)}</span></li>
              `)}
            </ul>
          </div>
          <pre class="code">${JSON.stringify(data.trace_fragment, null, 2)}</pre>
        `}
      </section>
    `;
  }

  // ---------------------------------------------------------------------
  // Tab 3 — Spend Mirror
  // ---------------------------------------------------------------------

  function SpendMirror() {
    const [sms, setSms] = useState(EXAMPLE_SMS);
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(false);

    const run = useCallback(async () => {
      setLoading(true); setErr(null);
      try {
        const lines = sms.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
        setData(await postJSON("/finance/parse_sms", { sms: lines }));
      } catch (e) { setErr(String(e)); }
      finally { setLoading(false); }
    }, [sms]);

    return html`
      <section>
        <h2>Spend Mirror</h2>
        <p class="muted">Paste UPI SMS strings. FinanceAgent regex pack parses + categorises.</p>
        <label class="field">UPI SMS strings (one per line)</label>
        <textarea rows="10" value=${sms} oninput=${e => setSms(e.target.value)}></textarea>
        <button class="primary" onclick=${run} disabled=${loading}>
          ${loading ? "Parsing…" : "Parse + categorise"}
        </button>
        ${err && html`<div class="status-banner error">${err}</div>`}
        ${data && html`
          <div class="aura-card">
            <div class="card-head">
              <span class="eyebrow">Spend Mirror</span>
              <span class="pill">₹${Number(data.total).toLocaleString()}</span>
            </div>
            <table class="aura-table">
              <thead><tr>
                <th>Merchant</th><th>Category</th><th>Bank</th><th>A/c</th><th class="right">Amount</th>
              </tr></thead>
              <tbody>
                ${(data.transactions || []).length === 0
                  ? html`<tr><td colspan="5" class="muted">No SMS parsed</td></tr>`
                  : data.transactions.map(t => html`
                      <tr>
                        <td>${t.merchant}</td>
                        <td>${t.category}</td>
                        <td>${t.bank}</td>
                        <td>**${t.account_last4}</td>
                        <td class="right">₹${Number(t.amount).toFixed(2)}</td>
                      </tr>`)
                }
              </tbody>
            </table>
            <p class="rationale">Parsed ${data.transactions.length} txn — ${data.skipped_count} unparsed.</p>
          </div>
        `}
      </section>
    `;
  }

  // ---------------------------------------------------------------------
  // Tab 4 — Load Score
  // ---------------------------------------------------------------------

  function LoadScore() {
    const [rmssd, setRmssd] = useState(28);
    const [entropy, setEntropy] = useState(4.8);
    const [switchRate, setSwitch] = useState(14);
    const [sleep, setSleep] = useState(120);
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(false);

    const run = useCallback(async () => {
      setLoading(true); setErr(null);
      try {
        setData(await postJSON("/wellness/load_score", {
          rmssd_ms: rmssd,
          typing_entropy: entropy,
          app_switch_rate: switchRate,
          sleep_debt_min: sleep,
        }));
      } catch (e) { setErr(String(e)); }
      finally { setLoading(false); }
    }, [rmssd, entropy, switchRate, sleep]);

    const score = data ? (data.payload.load_score || 0) : 0;
    const interv = data ? (data.payload.suggested_intervention || {}) : {};
    const drivers = data ? (data.payload.drivers || []) : [];

    return html`
      <section>
        <h2>Load Score</h2>
        <p class="muted">Slide the four headline features and watch the regressor + intervention picker.</p>

        <div class="slider-row">
          <label>RMSSD (ms)</label>
          <input type="range" min="15" max="80" value=${rmssd}
                 oninput=${e => setRmssd(Number(e.target.value))} />
          <span class="slider-val">${rmssd}</span>
        </div>
        <div class="slider-row">
          <label>Typing entropy (bits)</label>
          <input type="range" min="2" max="6" step="0.1" value=${entropy}
                 oninput=${e => setEntropy(Number(e.target.value))} />
          <span class="slider-val">${entropy.toFixed(1)}</span>
        </div>
        <div class="slider-row">
          <label>App switch rate</label>
          <input type="range" min="0" max="30" value=${switchRate}
                 oninput=${e => setSwitch(Number(e.target.value))} />
          <span class="slider-val">${switchRate}</span>
        </div>
        <div class="slider-row">
          <label>Sleep debt (min)</label>
          <input type="range" min="0" max="240" step="5" value=${sleep}
                 oninput=${e => setSleep(Number(e.target.value))} />
          <span class="slider-val">${sleep}</span>
        </div>

        <button class="primary" onclick=${run} disabled=${loading}>
          ${loading ? "Computing…" : "Recompute Load"}
        </button>
        ${err && html`<div class="status-banner error">${err}</div>`}

        ${data && html`
          <div class="aura-card">
            <div class="card-head">
              <span class="eyebrow">Load Score</span>
              <span class="pill ${pillTone(score)}">${score}</span>
            </div>
            <div class="grid-2">
              <div class="row"><span class="label">State</span><span class="value">${data.payload.state}</span></div>
              <div class="row"><span class="label">Intervention</span><span class="value">${interv.kind || "DO_NOTHING"}</span></div>
              <div class="row"><span class="label">Surface</span><span class="value">${interv.surface || "SILENT"}</span></div>
              <div class="row"><span class="label">Confirm</span><span class="value">${String(interv.confirm_required || false)}</span></div>
            </div>
            <ul class="bare">
              ${drivers.map(d => html`<li><span class="label">${d.feature}</span><span class="value">${d.value}</span></li>`)}
            </ul>
            <p class="rationale">${interv.rationale_seed || ""}</p>
          </div>
        `}
      </section>
    `;
  }

  // ---------------------------------------------------------------------
  // Shell + tab wiring
  // ---------------------------------------------------------------------

  function App() {
    const TABS = [
      { id: "brief", title: "Morning Brief", el: html`<${MorningBrief} />` },
      { id: "comms", title: "Quiet Group Chat", el: html`<${QuietGroup} />` },
      { id: "finance", title: "Spend Mirror", el: html`<${SpendMirror} />` },
      { id: "load", title: "Load Score", el: html`<${LoadScore} />` },
    ];
    const [tab, setTab] = useState("brief");
    const [apiUp, setApiUp] = useState(null);

    useEffect(() => {
      ping().then(setApiUp);
      const t = setInterval(() => ping().then(setApiUp), 8000);
      return () => clearInterval(t);
    }, []);

    return html`
      <${Hero} />
      <main class="aura-shell">
        <nav class="aura-nav">
          ${TABS.map(t => html`
            <button class=${tab === t.id ? "active" : ""} onclick=${() => setTab(t.id)}>
              ${t.title}
            </button>
          `)}
          <div class="status-banner ${apiUp ? "ok" : "error"}">
            ${apiUp == null ? "Probing API…" : apiUp ? "API: connected" : "API offline (start uvicorn)"}
          </div>
        </nav>
        <article>
          ${TABS.find(t => t.id === tab).el}
        </article>
        <${TraceOverlay} />
      </main>
      <footer class="aura-footer">
        Aura is on-device. This local demo runs on your Mac with zero internet egress.
      </footer>
    `;
  }

  // ---------------------------------------------------------------------
  // Mount
  // ---------------------------------------------------------------------

  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(html`<${App} />`);
})();
