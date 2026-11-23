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
  dhikrToday: "Each dhikr today",
  allTime: "all time",
  noDhikrToday: "No dhikr yet today",
  showAll: "Show all",
  more: "more",
  byPrayer: "By prayer time",
  mostAt: "Most at",
  nothingToday: "Nothing yet today",
  periods: "Periods",
  last14: "Last 14 days",
  updateApp: "Update the Wirid app on the phone to see this chart.",
  none14: "No dhikr in these 14 days yet",
  day: "day",
  active: "active",
  lastSession: "last session",
  synced: "Synced",
  familyToday: "Family today",
  noFamily: "No Wirid phones yet. Add one in Settings → Devices & services → Wirid.",
  title: "Title",
  phones: "Phones (none ticked = every phone)",
  nameFor: "Name for",
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

// Each dhikr today: coloured bars; "Show all" opens the ones not counted today.
const dhikrOf = (ctx) => core.dhikrList(ctx.hass.states, ctx.P, ctx.phone.name);
const dhikrKeys = (ctx) => dhikrOf(ctx).flatMap((d) => [d.entityId, d.allId]);

function dhikrBody(ctx) {
  const list = dhikrOf(ctx);
  const counted = list.filter((d) => d.today > 0), rest = list.filter((d) => !d.today);
  const max = Math.max(1, ...counted.map((d) => d.today));
  const rows = (ds) => ds.map((d) => `
    <div style="display:flex;align-items:center;gap:10px;opacity:${d.today ? 1 : 0.45}">
      <div style="width:28px;height:28px;border-radius:50%;background:${d.c};color:#06140F;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;flex:none">${esc(d.m)}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;justify-content:space-between;gap:8px;font-size:13px">
          <span class="ellipsis" style="font-weight:600">${esc(d.name)}</span>
          <span style="font-weight:700">${core.fmt(d.today)}</span>
        </div>
        <div style="height:6px;border-radius:3px;background:rgba(127,127,127,0.15);margin-top:4px">
          <div style="height:6px;border-radius:3px;width:${(d.today / max * 100).toFixed(1)}%;background:linear-gradient(90deg, ${d.c}99, ${d.c})"></div>
        </div>
        <div class="sec" style="margin-top:2px">${core.fmt(d.all)} ${STR.allTime}</div>
      </div>
    </div>`).join("");
  const top = counted.length
    ? `<div style="display:flex;flex-direction:column;gap:10px">${rows(counted)}</div>`
    : `<div class="note" style="font-size:13px">${STR.noDhikrToday}</div>`;
  const more = !rest.length ? "" : `
    <style>.all summary{list-style:none;cursor:pointer}.all summary::-webkit-details-marker{display:none}.chev{display:inline-block;transition:transform .15s}.all[open] .chev{transform:rotate(90deg)}</style>
    <details class="all"${ctx.ui.showAll ? " open" : ""}>
      <summary class="note" style="font-size:13px;margin-top:10px"><span class="chev">▸</span> ${STR.showAll} · ${rest.length} ${STR.more}</summary>
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:10px">${rows(rest)}</div>
    </details>`;
  return `<div class="title" style="margin-bottom:12px">${STR.dhikrToday}</div>${top}${more}`;
}

function dhikrAfter(root, ctx) {
  const d = root.querySelector("details.all");
  if (d) d.addEventListener("toggle", () => { ctx.ui.showAll = d.open; });
}

// By prayer time: nine columns, gold by day, blue at night.
const WAKTU = [["Sbh", "subuh"], ["Syk", "syuruk"], ["Dhu", "dhuha"], ["Zwl", "zawal"], ["Zhr", "zohor"],
  ["Asr", "asar"], ["Mgb", "maghrib"], ["Isy", "isyak"], ["Thj", "tahajjud"]];

function waktuBody(ctx) {
  const w = WAKTU.map(([l, k]) => ({ l, v: ctx.n(`today_${k}`), night: k === "isyak" || k === "tahajjud" }));
  const max = Math.max(1, ...w.map((x) => x.v));
  const top = w.reduce((a, b) => (b.v > a.v ? b : a), w[0]);
  const cols = w.map((x) => {
    const h = x.v ? Math.max(6, x.v / max * 90) : 4;
    const c = x.night ? "#8C9CFF" : "#FFC93C", tc = x.night ? ctx.pal.night : ctx.pal.gold;
    const lit = x === top && x.v;
    return `<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:4px">
        <div class="sec" style="font-size:10px;height:12px;white-space:nowrap">${x.v ? core.fmt(x.v) : ""}</div>
        <div style="height:90px;display:flex;align-items:flex-end;width:100%;justify-content:center">
          <div style="width:70%;max-width:22px;height:${h}px;border-radius:6px;background:${x.v ? `linear-gradient(180deg, ${c}, ${c}66)` : "rgba(127,127,127,0.15)"};${lit ? `box-shadow:0 0 10px ${c}88` : ""}"></div>
        </div>
        <div style="font-size:11px;color:${lit ? tc : "var(--secondary-text-color)"};font-weight:${lit ? 700 : 500}">${x.l}</div>
      </div>`;
  }).join("");
  return `<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px">
      <span class="title">${STR.byPrayer}</span>
      <span style="font-size:12px;color:${ctx.pal.gold};font-weight:600">${top.v ? `${STR.mostAt} ${top.l}` : STR.nothingToday}</span>
    </div>
    <div style="display:flex;gap:2px">${cols}</div>`;
}

// Periods: three totals with up/down pills.
const PERIODS = [["week", "7 days", "vs prev 7 days"], ["month", "Month", "vs last month"], ["year", "Year", "vs last year"]];

function periodsBody(ctx) {
  const tile = ([k, label, sub]) => {
    const ch = (ctx.hass.states[ctx.id(`${k}_change`)] || {}).state;
    const has = ch !== undefined && ch !== "" && !Number.isNaN(Number(ch));
    const v = Number(ch), up = v >= 0, c = up ? ctx.pal.up : ctx.pal.down;
    const pill = has ? `<span style="display:inline-block;max-width:100%;padding:2px 7px;border-radius:999px;background:${c}22;color:${c};font-size:11px;font-weight:700;white-space:nowrap">${up ? "▲" : "▼"} ${Math.abs(v)}%</span>` : "";
    return `<div style="flex:1 1 0;min-width:0;overflow:hidden;padding:10px 8px;border-radius:16px;background:rgba(127,127,127,0.08)">
        <div class="ellipsis" style="font-size:12px;color:var(--secondary-text-color);font-weight:600">${label}</div>
        <div class="ellipsis" style="font-size:clamp(16px, 5.2vw, 22px);font-weight:700;margin:4px 0 6px">${core.fmtCompact(ctx.n(`${k}_total`))}</div>
        ${pill}<div class="sec" style="font-size:10px;line-height:1.25;margin-top:4px;overflow-wrap:anywhere">${sub}</div>
      </div>`;
  };
  return `<div class="title" style="margin-bottom:10px">${STR.periods}</div>
    <div style="display:flex;gap:6px">${PERIODS.map(tile).join("")}</div>`;
}

const periodsKeys = (ctx) => PERIODS.flatMap(([k]) => [ctx.id(`${k}_total`), ctx.id(`${k}_change`)]);

// Last 14 days: one bar per day, stacked by dhikr in their app colours.
function daysBody(ctx) {
  const dates = (ctx.hass.states[ctx.phone.entityId].attributes || {}).days || [];
  const head = `<div class="title">${STR.last14}</div>`;
  if (!dates.length) return head + `<div class="note" style="margin-top:6px">${STR.updateApp}</div>`;
  const list = dhikrOf(ctx)
    .map((d) => {
      const days = dates.map((_, i) => (d.days ? d.days[i] || 0 : 0));
      return { ...d, days, sum: days.reduce((x, y) => x + y, 0) };
    })
    .filter((d) => d.sum > 0)
    .sort((a, b) => b.sum - a.sum);
  const totals = dates.map((_, i) => list.reduce((t, d) => t + d.days[i], 0));
  const all = totals.reduce((x, y) => x + y, 0);
  const max = Math.max(1, ...totals);
  const H = 110;
  const cols = dates.map((ds, i) => {
    const dt = new Date(ds + "T00:00:00");
    const last = i === dates.length - 1;
    const segs = list.filter((d) => d.days[i] > 0).map((d) =>
      `<div title="${esc(d.name)}: ${d.days[i]}" style="height:${(d.days[i] / max * H).toFixed(1)}px;background:${d.c}"></div>`).join("");
    return `<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:4px">
        <div class="sec" style="font-size:9px;height:11px;white-space:nowrap">${totals[i] ? core.fmtCompact(totals[i]) : ""}</div>
        <div style="height:${H}px;width:100%;display:flex;align-items:flex-end;justify-content:center">
          <div style="width:72%;max-width:18px;display:flex;flex-direction:column-reverse;border-radius:5px;overflow:hidden;${totals[i] ? "" : "height:3px;background:rgba(127,127,127,0.15)"}">${segs}</div>
        </div>
        <div style="font-size:10px;line-height:1.1;text-align:center;color:${last ? "var(--primary-text-color)" : "var(--secondary-text-color)"};font-weight:${last ? 700 : 500}">${"SMTWTFS"[dt.getDay()]}<br>${dt.getDate()}</div>
      </div>`;
  }).join("");
  const legend = list.map((d) => `<span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--secondary-text-color)">
      <span style="width:9px;height:9px;border-radius:50%;background:${d.c}"></span>${esc(d.name)} <b style="color:var(--primary-text-color)">${core.fmt(d.sum)}</b></span>`).join("");
  return `<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px">${head}
      <span class="sec" style="font-size:12px">${core.fmt(all)} · ${core.fmt(Math.round(all / dates.length))}/${STR.day}</span></div>
    <div style="display:flex;gap:2px">${cols}</div>
    <div style="display:flex;flex-wrap:wrap;gap:6px 12px;margin-top:10px">${legend || `<span class="sec">${STR.none14}</span>`}</div>`;
}

const daysKeys = (ctx) => [ctx.phone.entityId, ...dhikrOf(ctx).map((d) => d.entityId)];

// Summary: active days, last session, last sync.
const when = (iso, tz) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—"
    : `${new Intl.DateTimeFormat("en-GB", { timeZone: tz, weekday: "short" }).format(d)} ${core.clock(d, tz)}`;
};

function summaryBody(ctx) {
  const s = ctx.hass.states[ctx.id("last_session")] || { state: "", attributes: {} };
  const has = s.state && s.state !== "unavailable" && s.state !== "unknown";
  const item = (icon, c, big, small) => `<div style="flex:1;min-width:0;display:flex;align-items:center;gap:10px">
      <div style="width:34px;height:34px;border-radius:12px;background:${c}22;color:${c};display:flex;align-items:center;justify-content:center;flex:none">
        <ha-icon icon="${icon}" style="--mdc-icon-size:18px"></ha-icon></div>
      <div style="min-width:0"><div class="ellipsis" style="font-size:15px;font-weight:700">${big}</div>
      <div class="ellipsis sec">${small}</div></div></div>`;
  return `<div style="display:flex;gap:12px">
      ${item("mdi:calendar-check", ctx.pal.tier[0], `${core.fmt(ctx.n("active_days"))} ${STR.days}`, STR.active)}
      ${item("mdi:history", ctx.pal.minutes, has ? `${core.fmt(Number(s.state))} · ${esc(s.attributes.routine || "")}` : "—",
        `${STR.lastSession} ${when(s.attributes.ended, ctx.tz)}`)}
    </div>
    <div class="sec" style="font-size:10px;text-align:right;margin-top:8px">${STR.synced} ${when(ctx.phone.sent, ctx.tz)}</div>`;
}

const summaryKeys = (ctx) => [ctx.id("active_days"), ctx.id("last_session"), ctx.phone.entityId];

// Wirid (all): the six bodies in one card.
const ALL = [
  { body: todayBody, keys: (ctx) => todayKeys.map(ctx.id) },
  { body: dhikrBody, keys: dhikrKeys },
  { body: waktuBody, keys: (ctx) => WAKTU.map(([, k]) => ctx.id(`today_${k}`)) },
  { body: periodsBody, keys: periodsKeys },
  { body: daysBody, keys: daysKeys },
  { body: summaryBody, keys: summaryKeys },
];

function allBody(ctx) {
  const [today, ...rest] = ALL;
  const glow = ctx.status === "stale" ? "" : `background:${todayGlow(ctx)};`;
  return `<div style="margin:-16px -18px 0;padding:16px 18px;${glow}">${today.body(ctx)}</div>`
    + rest.map((s) => `<div class="divider"></div>${s.body(ctx)}`).join("");
}

// Wirid family: one row per phone.
const FAMILY_KEYS = ["today_total", "today_goal", "today_goal_percent", "streak_current"];
const initials = (name) => String(name).split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

function familyKeys(ctx) {
  return ctx.list.flatMap((p) => [p.entityId, ...FAMILY_KEYS.map((k) => `sensor.${p.prefix}${k}`)]);
}

function familyBody(ctx, el) {
  const rows = core.familyRows(ctx.list, ctx.hass.states, ctx.now, ctx.tz, ctx.config);
  el.style.display = "";
  if (!rows.length) {
    if (!el.preview) {
      el.style.display = "none";
      return "";
    }
    return `<ha-card><div class="note">${STR.noFamily}</div></ha-card>`;
  }
  const row = (r) => {
    const i = core.tierIndex(r.lap), col = TIERS[i];
    const under = r.lap > 1 ? TIERS[core.tierIndex(r.lap - 1)] + "80" : "rgba(127,127,127,0.15)";
    const line = r.status === "waiting" ? esc(STR.waiting)
      : r.status === "stale" ? esc(core.syncedLabel(r.sent, ctx.now, ctx.tz))
        : `<ha-icon icon="mdi:fire" style="--mdc-icon-size:13px;color:${ctx.pal.streak};vertical-align:-2px"></ha-icon> ${r.streak} ${STR.days} · `
          + `<span style="color:${ctx.pal.tier[i]};font-weight:600">${r.lap > 1 ? `×${r.lap} ${TIER_NAMES[i]}` : `${r.percent}%`}</span>`;
    return `<div style="display:flex;align-items:center;gap:10px;opacity:${r.status === "fresh" ? 1 : 0.55}">
        <div style="width:32px;height:32px;border-radius:50%;background:${col};color:#06140F;font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;flex:none">${esc(initials(r.name))}</div>
        <div style="flex:1;min-width:0">
          <div style="display:flex;justify-content:space-between;gap:8px;font-size:13px">
            <span class="ellipsis" style="font-weight:600">${esc(r.name)}</span><span style="font-weight:700">${core.fmt(r.total)}</span>
          </div>
          <div style="height:6px;border-radius:3px;background:${under};margin-top:4px">
            <div style="height:6px;border-radius:3px;width:${(Math.min(r.frac, 1) * 100).toFixed(1)}%;background:${col}"></div>
          </div>
          <div class="sec ellipsis" style="margin-top:3px">${line}</div>
        </div>
      </div>`;
  };
  return `<ha-card><div class="title" style="margin-bottom:12px">${esc(ctx.config.title || STR.familyToday)}</div>
    <div style="display:flex;flex-direction:column;gap:12px">${rows.map(row).join("")}</div></ha-card>`;
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

// ---------- editor: the family card ----------

class WiridFamilyEditor extends HTMLElement {
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
    const list = core.phones(this._hass.states, this._hass.entities, this._hass.devices);
    const chosen = Array.isArray(this._config.phones) ? this._config.phones : [];
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => (s.name === "title" ? STR.title : s.name === "phones" ? STR.phones
        : `${STR.nameFor} ${(list.find((p) => `name_${p.prefix}` === s.name) || {}).name || ""}`);
      this._form.addEventListener("value-changed", (ev) => {
        const v = ev.detail.value;
        const config = { ...this._config };
        if (v.title) config.title = v.title;
        else delete config.title;
        const prefixes = v.phones || [];
        if (prefixes.length) {
          config.phones = prefixes.map((prefix) => {
            const name = (v[`name_${prefix}`] || "").trim();
            return name ? { prefix, name } : { prefix };
          });
        } else delete config.phones;
        this._config = config;
        fire(this, "config-changed", { config });
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = [
      { name: "title", selector: { text: {} } },
      { name: "phones", selector: { select: { multiple: true, options: list.map((p) => ({ value: p.prefix, label: p.name })) } } },
      ...chosen.map((c) => ({ name: `name_${c.prefix}`, selector: { text: {} } })),
    ];
    const data = { title: this._config.title || "", phones: chosen.map((c) => c.prefix) };
    chosen.forEach((c) => { data[`name_${c.prefix}`] = c.name || ""; });
    this._form.data = data;
  }
}

// ---------- registration ----------

const CARDS = [
  { type: "wirid-today-card", name: "Wirid today", description: "Today's ring, goal tier, streak, minutes and sessions.",
    spec: { keys: (ctx) => todayKeys.map(ctx.id), body: todayBody, glow: todayGlow, size: 3 } },
  { type: "wirid-dhikr-card", name: "Wirid dhikr", description: "Each dhikr counted today, in its app colour.",
    spec: { keys: dhikrKeys, body: dhikrBody, after: dhikrAfter, size: 4 } },
  { type: "wirid-waktu-card", name: "Wirid prayer times", description: "Today's dhikr in each of the nine waktu.",
    spec: { keys: (ctx) => WAKTU.map(([, k]) => ctx.id(`today_${k}`)), body: waktuBody, size: 3 } },
  { type: "wirid-periods-card", name: "Wirid periods", description: "Last 7 days, month and year, with the change.",
    spec: { keys: periodsKeys, body: periodsBody, size: 2 } },
  { type: "wirid-days-card", name: "Wirid 14 days", description: "The last 14 days, stacked by dhikr.",
    spec: { keys: daysKeys, body: daysBody, size: 4 } },
  { type: "wirid-summary-card", name: "Wirid summary", description: "Active days, the last session and the last sync.",
    spec: { keys: summaryKeys, body: summaryBody, size: 1 } },
  { type: "wirid-card", name: "Wirid (all)", description: "All six Wirid cards in one, for a quick start.",
    spec: { keys: (ctx) => ALL.flatMap((s) => s.keys(ctx)), body: allBody, after: dhikrAfter, size: 16 } },
  { type: "wirid-family-card", name: "Wirid family", description: "Every phone's day at a glance, one row each.",
    spec: { family: true, keys: familyKeys, body: familyBody, editor: "wirid-family-editor", size: 3 } },
];

const define = (tag, cls) => {
  if (!customElements.get(tag)) customElements.define(tag, cls);
};
define("wirid-phone-editor", WiridPhoneEditor);
define("wirid-family-editor", WiridFamilyEditor);
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
