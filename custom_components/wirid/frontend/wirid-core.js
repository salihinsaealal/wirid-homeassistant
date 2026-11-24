// Pure helpers for the Wirid cards: no DOM, tested with `node --test tests/js/*.test.mjs`.

/** Tier colours for laps 1..5+ (the app's; sensor keys emerald, gold, blue, pink, silver). */
export const TIERS = ["#34E3A0", "#FFD84D", "#3FA9FF", "#FF9ECF", "#E4ECF7"];
/** What each lap is called on the cards: words of praise rising with the level, as in the app (never colour names). */
export const TIER_NAMES = ["On the way", "Goal reached!", "Excellent!", "Outstanding!", "Extraordinary!", "Phenomenal!"];

export function tierName(lap) {
  return TIER_NAMES[Math.min(Math.max(lap, 1), TIER_NAMES.length) - 1];
}
export const DHIKR_FALLBACK = "#9AA4B1";

const DARK_TEXT = {
  tier: TIERS, gold: "#FFC93C", night: "#8C9CFF", up: "#34E3A0", down: "#FF6B86",
  minutes: "#5CC8FF", streak: "#FF8A4C", sessions: "#B48CFF",
};
// Same hues, dark enough for text on a light card (each ≥4.5:1 on white).
const LIGHT_TEXT = {
  tier: ["#0B7A55", "#8A6400", "#1559B8", "#B8326F", "#4E5D73"], gold: "#8A6200", night: "#4453C4",
  up: "#0B7A55", down: "#C42A50", minutes: "#0A6FA3", streak: "#B8521A", sessions: "#6B3FC6",
};

/** Colours for text; rings, bars and discs always use the dark (app) colours. */
export function palette(dark) {
  return dark ? DARK_TEXT : LIGHT_TEXT;
}

/** Which goal lap today's total is on, and how far through it (0..1). Reaching the goal opens the next lap (app 0.11). */
export function lapOf(total, goal) {
  if (!(goal > 0)) return { lap: 1, frac: 0 };
  if (total < goal) return { lap: 1, frac: total / goal };
  const lap = Math.floor(total / goal) + 1;
  return { lap, frac: (total - (lap - 1) * goal) / goal };
}

export function tierIndex(lap) {
  return Math.min(Math.max(lap, 1), 5) - 1;
}

const time = (s) => {
  const t = Date.parse(s);
  return Number.isNaN(t) ? -Infinity : t;
};

/** Every Wirid phone: one per `last_sent` sensor carrying a `wirid_prefix`. */
export function phones(states, entities = {}, devices = {}) {
  return Object.values(states)
    .filter((s) => s.entity_id.endsWith("last_sent") && s.attributes && s.attributes.wirid_prefix)
    .map((s) => {
      const dev = devices[(entities[s.entity_id] || {}).device_id];
      const name = (dev && (dev.name_by_user || dev.name))
        || (s.attributes.friendly_name || s.attributes.wirid_prefix).replace(/ Last sent$/, "");
      return { prefix: s.attributes.wirid_prefix, name, userId: s.attributes.wirid_user_id || null,
        sent: s.state, entityId: s.entity_id };
    });
}

/** The phone a card shows: the chosen one, else the viewer's newest. */
export function resolvePhone(list, userId, chosen) {
  if (chosen) {
    const phone = list.find((p) => p.prefix === chosen);
    return phone ? { phone, status: "ok" } : { phone: null, status: "missing" };
  }
  const mine = list.filter((p) => userId && p.userId === userId).sort((a, b) => time(b.sent) - time(a.sent));
  return mine.length ? { phone: mine[0], status: "ok" } : { phone: null, status: "none" };
}

export function readNumber(states, entityId) {
  return Number((states[entityId] || {}).state) || 0;
}

/** "YYYY-MM-DD" of a moment in a time zone. */
export function dayKey(at, tz) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" })
    .format(at instanceof Date ? at : new Date(at));
}

function dayBefore(key) {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d - 1)).toISOString().slice(0, 10);
}

/** "fresh" (synced today in HA's zone), "stale" (before today) or "waiting" (never synced). */
export function phoneStatus(sentIso, now, tz) {
  if (time(sentIso) === -Infinity) return "waiting";
  return dayKey(sentIso, tz) < dayKey(now, tz) ? "stale" : "fresh";
}

export function clock(at, tz) {
  return new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "numeric", minute: "2-digit", hour12: true })
    .format(new Date(at)).replace(/\s?([ap])\.?m\.?$/i, (_, x) => ` ${x.toLowerCase()}m`);
}

export function syncedLabel(sentIso, now, tz) {
  const sentDay = dayKey(sentIso, tz), today = dayKey(now, tz);
  if (sentDay === today) return `Last synced today ${clock(sentIso, tz)}`;
  if (sentDay === dayBefore(today)) return `Last synced yesterday ${clock(sentIso, tz)}`;
  const date = new Intl.DateTimeFormat("en-GB", { timeZone: tz, weekday: "short", day: "numeric", month: "short" })
    .format(new Date(sentIso)).replace(",", "");
  return `Last synced ${date}, ${clock(sentIso, tz)}`;
}

export function fmt(n) {
  return Number(n).toLocaleString();
}

/** Totals of 100,000+ in short form (1.2M) so narrow tiles always fit them. */
export function fmtCompact(n) {
  return n >= 100000
    ? new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(n)
    : fmt(n);
}

/** This phone's dhikr (one per `*_today` sensor), most counted today first. */
export function dhikrList(states, prefix, owner) {
  return Object.values(states)
    .filter((s) => s.entity_id.endsWith("_today") && s.attributes && s.attributes.slug
      && s.attributes.wirid_prefix === prefix)
    .map((s) => {
      const a = s.attributes;
      let name = (a.friendly_name || a.slug).replace(/ today$/, "");
      if (owner && name.startsWith(owner + " ")) name = name.slice(owner.length + 1);
      const c = /^#[0-9a-fA-F]{6}$/.test(a.color || "") ? a.color : DHIKR_FALLBACK;
      const m = a.mono || name.replace(/[^\p{L}\p{N}]/gu, "").slice(0, 2).toUpperCase();
      const allId = a.all_time_entity || `sensor.${prefix}${a.slug}_all_time`;
      return { name, c, m, today: Number(s.state) || 0, all: readNumber(states, allId), allId,
        days: Array.isArray(a.days) ? a.days.map((v) => Number(v) || 0) : null, entityId: s.entity_id };
    })
    .sort((a, b) => b.today - a.today || b.all - a.all);
}

/** Rows for the family card: config order when phones are chosen, else fresh by today's total, then the rest. */
export function familyRows(list, states, now, tz, config = {}) {
  const row = (p, name) => {
    const n = (k) => readNumber(states, `sensor.${p.prefix}${k}`);
    const total = n("today_total"), goal = n("today_goal");
    return { prefix: p.prefix, name: name || p.name, total, goal, ...lapOf(total, goal),
      streak: n("streak_current"), percent: n("today_goal_percent"),
      status: phoneStatus(p.sent, now, tz), sent: p.sent };
  };
  if (Array.isArray(config.phones) && config.phones.length) {
    return config.phones
      .map((c) => [list.find((p) => p.prefix === c.prefix), c.name])
      .filter(([p]) => p)
      .map(([p, name]) => row(p, name));
  }
  const rows = list.map((p) => row(p));
  const fresh = rows.filter((r) => r.status === "fresh").sort((a, b) => b.total - a.total);
  return fresh.concat(rows.filter((r) => r.status !== "fresh"));
}
