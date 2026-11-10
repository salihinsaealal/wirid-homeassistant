<p align="center"><img src="custom_components/wirid/brand/icon.png" width="96" alt="Wirid icon"></p>

# Wirid for Home Assistant

Your dhikr statistics from the **Wirid** Android app, in Home Assistant. Wirid counts dhikr with a small Bluetooth keypad, even with the phone in your pocket and the screen off. This integration gives each phone its own device, with today's total, your goal, every waktu, each dhikr, weekly, monthly and yearly totals, and your streaks.

- **One device per phone,** so a family can each have their own.
- **Tied to a person:** link each phone to a Home Assistant user, and one shared dashboard shows every person their own stats.
- **No YAML.** Everything is set up from the UI. A dhikr you start using appears by itself.
- **Stats only:** no live counting, no location. The phone sends a snapshot after each session, when the app opens, every hour and at midnight.

## Install

**Home Assistant 2026.11 or newer (Marketplace):** Settings → Marketplace → **Add from link** → `https://github.com/salihinsaealal/wirid-homeassistant` → Install → restart Home Assistant.

**Older Home Assistant with HACS:** HACS → ⋮ → Custom repositories → add `https://github.com/salihinsaealal/wirid-homeassistant` as an *Integration* → install **Wirid** → restart.

## Connect a phone

1. Settings → Devices & services → **Add integration** → **Wirid**.
2. Give the phone a name (e.g. "Salihin's phone").
3. Choose who uses it (a Home Assistant user), or *Nobody*.
4. Copy the address shown at the end.
5. In Wirid on the phone: Settings → Home Assistant → **Webhook URL** → paste it, then turn on **Send stats to Home Assistant**.

The address only works for that phone. The integration's **Configure** button shows it again, links the phone to a different person, or makes a **new address** (the old one stops working at once; use it if the address was shared by mistake).

> The address step has no "open in Wirid" link: Home Assistant only allows `http(s)`, `mailto` and similar links in setup screens, so copy and paste is the way in.

Home Assistant needs an address the phone can reach. Set it under Settings → System → Network (the *Home Assistant URL*). If you use it away from home, that must be your external URL.

## Moving from the YAML setup

If you used Wirid's earlier "Copy HA config" (template sensors in `configuration.yaml`), you can keep all your history:

1. Remove the Wirid block under `template:` in `configuration.yaml`.
2. Restart Home Assistant.
3. Add the Wirid integration. On the first phone it finds the old sensors and offers **Take over**. Choose it.

Your phone keeps the same entity names (`sensor.wirid_today_total` and so on), so graphs and long-term statistics continue where they were. Taken-over entities keep their exact old IDs, including ones Home Assistant derived from the dhikr's name (`sensor.wirid_allahu_akbar_all_time`) and ones you renamed. If the old block is still loaded, the integration refuses to continue until it's gone, because otherwise you'd get duplicate `_2` sensors.

## Entities

Each phone's entities start with its prefix: `sensor.wirid_` for the first phone, `sensor.wirid_<name>_` for the others (fixed when the phone is added).

| Entity | Meaning | Unit |
|---|---|---|
| `today_total`, `today_goal`, `today_goal_percent` | Today and your daily goal | dhikr, % |
| `today_tier` | `emerald` up to the goal, `gold` past it, `purple` past twice | |
| `today_sessions`, `today_minutes` | Sessions and time today | sessions, min |
| `today_subuh` … `today_tahajjud` | Today by waktu (9) | dhikr |
| `<dhikr>_today`, `<dhikr>_all_time` | Each dhikr you've used (`_today` carries `all_time_entity`, its pair's ID) | dhikr |
| `week_total`, `month_total`, `year_total` | Period totals | dhikr |
| `week_change`, `month_change`, `year_change` | Change from the previous period | % |
| `streak_current`, `streak_best`, `active_days` | Consistency | days |
| `last_session` | Count of the last session (routine and end time as attributes) | dhikr |
| `last_sent` | When the phone last sent (diagnostic) | |

Only `*_all_time` are totals for long-term statistics, so Home Assistant can graph each dhikr by day, week or month.

## Dashboard

`dashboard/wirid-cards.yaml` holds the colourful cards (today's ring, each dhikr, waktu, periods, last 14 days, consistency). They need [button-card](https://github.com/custom-cards/button-card) (Marketplace / HACS).

Paste the items under a view's `cards:`. Every card finds the phone linked to whoever is looking: you see your stats, your family see theirs, and someone with no phone sees nothing.

The "Last 14 days" card draws each day as a bar stacked by dhikr, in the app's colours. It follows the viewer like the others, so there is nothing to edit; it needs Wirid app 0.3.0 or newer on the phone.

## Payload (for developers)

The phone POSTs one JSON snapshot to `/api/webhook/<id>`:

```json
{"v":1,"sent":"2026-11-10T12:42:21+08:00","app":"0.4.0",
 "today":{"total":398,"goal":1000,"goal_percent":39,"tier":"emerald","sessions":13,"minutes":22,
          "waktu":{"subuh":10,"dhuha":388}},
 "dhikr":{"subhanallah":{"name":"SubhanAllah","today":33,"all_time":4000,"color":"#34E3A0","mono":"SA","days":[0,…,33]}},
 "week":{"total":2000,"change":-12},"month":{"total":9000,"change":null},"year":{"total":40000,"change":5},
 "streak":{"current":1,"best":9,"active_days":40},
 "last_session":{"routine":"Istighfar ×100","count":60,"ended":"2026-11-10T12:37:18+08:00"},
 "days":["2026-10-28","…","2026-11-10"]}
```

`app`, `color`, `mono` and `days` (the last 14 days: dates at the top level, counts per dhikr, oldest first) are optional; older app versions don't send them. Unknown fields and higher `v` are tolerated.

## Privacy

Only the stats above leave the phone, and only to your Home Assistant. No location, no live counting, no third parties. Anyone who has a phone's address can post numbers to it, as with any webhook; make a new address if it leaks.

## Get the app

Wirid for Android: download link coming soon.

## Licence

MIT
