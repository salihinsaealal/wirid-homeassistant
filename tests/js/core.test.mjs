// Pure helpers behind the Wirid cards. Run: node --test tests/js/
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  lapOf, tierIndex, palette, TIERS, phones, resolvePhone, readNumber,
  phoneStatus, syncedLabel, fmtCompact, dhikrList, familyRows,
} from "../../custom_components/wirid/frontend/wirid-core.js";

const KL = "Asia/Kuala_Lumpur";
const sent = (prefix, at, userId = "u1") => ({
  entity_id: `sensor.${prefix}last_sent`, state: at,
  attributes: { wirid_prefix: prefix, wirid_user_id: userId, friendly_name: `${prefix} Last sent` },
});
const num = (id, v, attributes = {}) => ({ entity_id: id, state: String(v), attributes });
const byId = (...ss) => Object.fromEntries(ss.map((s) => [s.entity_id, s]));

test("lapOf: under, past and exactly at the goal laps", () => {
  assert.deepEqual(lapOf(398, 1000), { lap: 1, frac: 0.398 });
  assert.equal(lapOf(1398, 1000).lap, 2);
  assert.ok(Math.abs(lapOf(1398, 1000).frac - 0.398) < 1e-9);
  assert.deepEqual(lapOf(2000, 1000), { lap: 2, frac: 1 });
  assert.equal(lapOf(6200, 1000).lap, 7);
  assert.equal(tierIndex(7), 4);
  assert.deepEqual(lapOf(5, 0), { lap: 1, frac: 0 });
});

test("palette: exact colours in dark, darker text in light", () => {
  assert.equal(palette(true).tier[1], "#FFD84D");
  assert.equal(palette(false).tier[1], "#8A6400");
  assert.equal(palette(false).tier[4], "#4E5D73");
  assert.equal(TIERS[3], "#FF9ECF");
});

test("phones: name from the device registry, else the friendly name", () => {
  const states = byId(sent("wirid_", "2026-11-23T10:00:00+08:00"), sent("wirid_umi_", "2026-11-23T09:00:00+08:00", "u2"),
    num("sensor.other_last_sent", 1));
  const entities = { "sensor.wirid_last_sent": { device_id: "d1" } };
  const devices = { d1: { name: "Salihin's phone", name_by_user: null } };
  const list = phones(states, entities, devices);
  assert.equal(list.length, 2);
  assert.equal(list.find((p) => p.prefix === "wirid_").name, "Salihin's phone");
  assert.equal(list.find((p) => p.prefix === "wirid_umi_").name, "wirid_umi_");
});

test("resolvePhone: newest of the viewer's phones; unknown sorts last", () => {
  const list = phones(byId(sent("wirid_", "2026-11-23T10:00:00+08:00"), sent("wirid_b_", "2026-11-23T11:00:00+08:00"),
    sent("wirid_c_", "unknown")), {}, {});
  assert.equal(resolvePhone(list, "u1").phone.prefix, "wirid_b_");
  const two = phones(byId(sent("wirid_c_", "unknown"), sent("wirid_", "2026-11-23T10:00:00+08:00")), {}, {});
  assert.equal(resolvePhone(two, "u1").phone.prefix, "wirid_");
});

test("resolvePhone: chosen phone, missing phone, no phone", () => {
  const list = phones(byId(sent("wirid_", "2026-11-23T10:00:00+08:00")), {}, {});
  assert.equal(resolvePhone(list, "zz", "wirid_").status, "ok");
  assert.equal(resolvePhone(list, "u1", "wirid_umi_").status, "missing");
  assert.deepEqual(resolvePhone(list, "nobody"), { phone: null, status: "none" });
});

test("readNumber: missing or unavailable reads 0", () => {
  assert.equal(readNumber({}, "sensor.wirid_today_total"), 0);
  assert.equal(readNumber(byId(num("sensor.x", "unavailable")), "sensor.x"), 0);
  assert.equal(readNumber(byId(num("sensor.x", 42)), "sensor.x"), 42);
});

test("phoneStatus: stale by Home Assistant's date, not the browser's", () => {
  const s = "2026-11-22T23:40:00+08:00";
  assert.equal(phoneStatus(s, new Date("2026-11-23T01:00:00+08:00"), KL), "stale");
  assert.equal(phoneStatus(s, new Date("2026-11-22T23:50:00+08:00"), KL), "fresh");
  assert.equal(phoneStatus(s, new Date("2026-11-23T01:00:00+08:00"), "Europe/London"), "fresh");
  assert.equal(phoneStatus("unknown", new Date(), KL), "waiting");
});

test("syncedLabel: yesterday, or the date when older", () => {
  const now = new Date("2026-11-23T01:00:00+08:00");
  assert.equal(syncedLabel("2026-11-22T23:40:00+08:00", now, KL), "Last synced yesterday 11:40 pm");
  assert.equal(syncedLabel("2026-11-17T23:40:00+08:00", now, KL), "Last synced Tue 17 Nov, 11:40 pm");
});

test("fmtCompact: short form from 100,000", () => {
  assert.equal(fmtCompact(99999), (99999).toLocaleString());
  assert.equal(fmtCompact(1234567), "1.2M");
});

test("dhikrList: this phone's dhikr, owner name stripped, sorted by today", () => {
  const states = byId(
    num("sensor.wirid_subhanallah_today", 33, { slug: "subhanallah", wirid_prefix: "wirid_", color: "#34E3A0", mono: "SA",
      friendly_name: "Phone SubhanAllah today", all_time_entity: "sensor.wirid_subhanallah_all_time" }),
    num("sensor.wirid_subhanallah_all_time", 4000),
    num("sensor.wirid_istighfar_today", 100, { slug: "istighfar", wirid_prefix: "wirid_", color: "bad",
      friendly_name: "Phone Istighfar today" }),
    num("sensor.wirid_umi_x_today", 999, { slug: "x", wirid_prefix: "wirid_umi_", friendly_name: "X today" }),
  );
  const list = dhikrList(states, "wirid_", "Phone");
  assert.deepEqual(list.map((d) => d.name), ["Istighfar", "SubhanAllah"]);
  assert.equal(list[0].c, "#9AA4B1");
  assert.equal(list[0].m, "IS");
  assert.equal(list[1].all, 4000);
});

test("familyRows: fresh by today's total, stale last", () => {
  const now = new Date("2026-11-23T12:00:00+08:00");
  const states = byId(
    sent("wirid_a_", "2026-11-23T10:00:00+08:00"), num("sensor.wirid_a_today_total", 650), num("sensor.wirid_a_today_goal", 1000),
    sent("wirid_b_", "2026-11-22T22:00:00+08:00"), num("sensor.wirid_b_today_total", 1400), num("sensor.wirid_b_today_goal", 1000),
    sent("wirid_c_", "2026-11-23T09:00:00+08:00"), num("sensor.wirid_c_today_total", 200), num("sensor.wirid_c_today_goal", 1000),
  );
  const list = phones(states, {}, {});
  assert.deepEqual(familyRows(list, states, now, KL, {}).map((r) => r.total), [650, 200, 1400]);
  const rows = familyRows(list, states, now, KL, { phones: [{ prefix: "wirid_c_", name: "Aisyah" }, { prefix: "wirid_a_" }] });
  assert.deepEqual(rows.map((r) => r.name), ["Aisyah", "wirid_a_"]);
  assert.equal(rows[0].status, "fresh");
});
