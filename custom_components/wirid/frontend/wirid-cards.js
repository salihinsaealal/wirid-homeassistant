// Wirid dashboard cards. Served and loaded by the Wirid integration; no build step, no libraries.
// The pure helpers live in wirid-core.js (tested with node --test); this file is the DOM side.

const VERSION = new URL(import.meta.url).searchParams.get("v") || "dev";
const core = await import(new URL("./wirid-core.js" + new URL(import.meta.url).search, import.meta.url).href);
const { TIERS, TIER_NAMES } = core;

// Every word the cards show, in one place so a translation can be added later.
const STR = {
  viewer: "Whoever is looking",
  phone: "Phone",
  noPhone: "Link a phone to your user in the Wirid integration to see your stats here.",
  missing: "Phone not found. Pick another phone in the card's settings.",
  waiting: "Waiting for the first sync from the phone.",
  today: "Wirid today",
  of: "of",
  lap: "lap",
  days: "days",
  best: "best",
  min: "min",
  sessions: "sessions",
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)).join(",");

const CSS = `
  :host { display: block; }
  ha-card { padding: 16px 18px; overflow: hidden; color: var(--primary-text-color); }
  .title { font-size: 15px; font-weight: 700; color: var(--primary-text-color); }
  .note { font-size: 12px; color: var(--secondary-text-color); }
  .synced { font-size: 11px; color: var(--secondary-text-color); margin-bottom: 8px; }
  .stale { opacity: .55; }
  .sec { font-size: 11px; color: var(--secondary-text-color); }
  .chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; }
  .chip ha-icon { --mdc-icon-size: 14px; }
  .ellipsis { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .divider { height: 1px; background: var(--divider-color, rgba(127,127,127,.2)); margin: 16px -18px; }
`;

// ---------- card bodies: each returns HTML for one phone ----------

const chip = (icon, text, c) =>
  `<span class="chip" style="background:${c}22;color:${c}"><ha-icon icon="${icon}"></ha-icon>${esc(text)}</span>`;

const todayKeys = ["today_total", "today_goal", "today_goal_percent", "streak_current", "streak_best", "today_minutes", "today_sessions"];

function todayBody(ctx) {
  const { n, pal } = ctx;
  const total = n("today_total"), goal = n("today_goal");
  const { lap, frac } = core.lapOf(total, goal);
  const i = core.tierIndex(lap);
  const ring = TIERS[i], under = lap > 1 ? TIERS[core.tierIndex(lap - 1)] : null, text = pal.tier[i];
  const r = 50, C = 2 * Math.PI * r, dash = (C * Math.min(frac, 1)).toFixed(1);
  return `
    <div style="display:flex;align-items:center;gap:18px">
      <div style="position:relative;width:124px;height:124px;flex:none">
        <svg viewBox="0 0 124 124" width="124" height="124" style="transform:rotate(-90deg)">
          <circle cx="62" cy="62" r="${r}" fill="none" stroke="${under ? under + "66" : "rgba(127,127,127,0.15)"}" stroke-width="11"/>
          <circle cx="62" cy="62" r="${r}" fill="none" stroke="${ring}" stroke-width="11" stroke-linecap="round"
                  stroke-dasharray="${dash} ${C.toFixed(1)}" style="filter:drop-shadow(0 0 6px ${ring}aa)"/>
        </svg>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
          <div style="font-size:30px;font-weight:700;letter-spacing:-1px">${core.fmt(total)}</div>
          <div class="sec">${STR.of} ${core.fmt(goal)}</div>
        </div>
      </div>
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:8px">
        <div style="font-size:13px;color:var(--secondary-text-color);font-weight:600">${STR.today}</div>
        <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">
          <span style="font-size:26px;font-weight:700;color:${text}">${n("today_goal_percent")}%</span>
          <span style="font-size:13px;color:${text};font-weight:600">${TIER_NAMES[i]}${lap > 1 ? ` · ${STR.lap} ${lap}` : ""}</span>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${chip("mdi:fire", `${n("streak_current")} ${STR.days}`, pal.streak)}
          ${chip("mdi:trophy-outline", `${STR.best} ${n("streak_best")}`, pal.tier[1])}
          ${chip("mdi:timer-outline", `${n("today_minutes")} ${STR.min}`, pal.minutes)}
          ${chip("mdi:repeat", `${n("today_sessions")} ${STR.sessions}`, pal.sessions)}
        </div>
      </div>
    </div>`;
}

function todayGlow(ctx) {
  const { lap } = core.lapOf(ctx.n("today_total"), ctx.n("today_goal"));
  const c = rgb(TIERS[core.tierIndex(lap)]);
  return `radial-gradient(120% 140% at 0% 0%, rgba(${c},0.22) 0%, rgba(${c},0.04) 55%, var(--ha-card-background, var(--card-background-color)) 100%)`;
}

// ---------- the shared card element ----------

const fire = (el, type, detail) => el.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));

class WiridCard extends HTMLElement {
  // Each card class sets static spec = { keys(ctx) -> entity ids, body(ctx) -> html, glow?(ctx) -> css, after?, size }.
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._ui = {};
  }

  setConfig(config) {
    this._config = { ...(config || {}) };
    this._sig = null;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  get hass() {
    return this._hass;
  }

  connectedCallback() {
    // Midnight turns a phone stale without any state change, so re-check once a minute.
    clearInterval(this._tick);
    this._tick = setInterval(() => this._render(), 60000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  getCardSize() {
    return this.constructor.spec.size || 3;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  static getConfigElement() {
    return document.createElement("wirid-phone-editor");
  }

  static getStubConfig() {
    return {};
  }

  _context() {
    const hass = this._hass;
    const list = core.phones(hass.states, hass.entities, hass.devices);
    const { phone, status } = core.resolvePhone(list, hass.user && hass.user.id, this._config.phone);
    const tz = (hass.config && hass.config.time_zone) || Intl.DateTimeFormat().resolvedOptions().timeZone;
    const now = new Date();
    const dark = !!(hass.themes && hass.themes.darkMode);
    const P = phone ? phone.prefix : null;
    return {
      hass, phone, P, now, tz, dark, list, ui: this._ui, config: this._config,
      status: phone ? core.phoneStatus(phone.sent, now, tz) : status,
      pal: core.palette(dark),
      n: (objectId) => core.readNumber(hass.states, `sensor.${P}${objectId}`),
      id: (objectId) => `sensor.${P}${objectId}`,
    };
  }

  _render() {
    if (!this._hass || !this._config) return;
    const ctx = this._context();
    const spec = this.constructor.spec;
    const ids = ctx.P || spec.family ? spec.keys(ctx) : [];
    const states = this._hass.states;
    // Re-render only when something this card reads has changed.
    const sig = JSON.stringify([ctx.status, ctx.P, ctx.dark, !!this.preview, this._config, core.dayKey(ctx.now, ctx.tz),
      ctx.phone && ctx.phone.sent, ids.map((id) => states[id] && [states[id].state, states[id].last_updated])]);
    if (sig === this._sig) return;
    this._sig = sig;
    this.shadowRoot.innerHTML = `<style>${CSS}</style>${spec.family ? spec.body(ctx, this) : this._html(ctx, spec)}`;
    const card = this.shadowRoot.querySelector("ha-card");
    if (card && spec.glow && ctx.P && (ctx.status === "fresh" || ctx.status === "stale")) card.style.background = spec.glow(ctx);
    if (spec.after) spec.after(this.shadowRoot, ctx);
  }

  _html(ctx, spec) {
    this.style.display = "";
    if (ctx.status === "none") {
      if (!this.preview) {
        this.style.display = "none";
        return "";
      }
      return `<ha-card><div class="note">${STR.noPhone}</div></ha-card>`;
    }
    if (ctx.status === "missing") return `<ha-card><div class="note">${STR.missing}</div></ha-card>`;
    if (ctx.status === "waiting") return `<ha-card><div class="note">${STR.waiting}</div></ha-card>`;
    const stale = ctx.status === "stale";
    const synced = stale ? `<div class="synced">${esc(core.syncedLabel(ctx.phone.sent, ctx.now, ctx.tz))}</div>` : "";
    return `<ha-card>${synced}<div class="${stale ? "stale" : ""}">${spec.body(ctx)}</div></ha-card>`;
  }
}

// ---------- editor: which phone ----------

class WiridPhoneEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = () => STR.phone;
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...this._config };
        const v = ev.detail.value.phone;
        if (!v || v === "viewer") delete config.phone;
        else config.phone = v;
        this._config = config;
        fire(this, "config-changed", { config });
      });
      this.appendChild(this._form);
    }
    const list = core.phones(this._hass.states, this._hass.entities, this._hass.devices);
    this._form.hass = this._hass;
    this._form.schema = [{
      name: "phone",
      selector: { select: { mode: "dropdown", options: [{ value: "viewer", label: STR.viewer },
        ...list.map((p) => ({ value: p.prefix, label: p.name }))] } },
    }];
    this._form.data = { phone: this._config.phone || "viewer" };
  }
}

// ---------- registration ----------

const CARDS = [
  { type: "wirid-today-card", name: "Wirid today", description: "Today's ring, goal tier, streak, minutes and sessions.",
    spec: { keys: (ctx) => todayKeys.map(ctx.id), body: todayBody, glow: todayGlow, size: 3 } },
];

const define = (tag, cls) => {
  if (!customElements.get(tag)) customElements.define(tag, cls);
};
define("wirid-phone-editor", WiridPhoneEditor);
window.customCards = window.customCards || [];
for (const c of CARDS) {
  define(c.type, class extends WiridCard {
    static spec = c.spec;
    static getConfigElement() {
      return document.createElement(c.spec.editor || "wirid-phone-editor");
    }
  });
  if (!window.customCards.some((x) => x.type === c.type)) {
    window.customCards.push({ type: c.type, name: c.name, description: c.description, preview: true,
      documentationURL: "https://github.com/salihinsaealal/wirid-homeassistant#dashboard" });
  }
}

console.info(`%c Wirid cards %c ${VERSION} `, "background:#34E3A0;color:#06140F;font-weight:700", "");
