<p align="center"><img src="custom_components/wirid/brand/icon.png" width="96" alt="Wirid icon"></p>

# Wirid for Home Assistant

Your dhikr statistics from the **Wirid** Android app, in Home Assistant. Wirid counts dhikr with a small Bluetooth keypad, even with the phone in your pocket and the screen off. This integration gives each phone its own device, with today's total, your goal, every waktu, each dhikr, weekly, monthly and yearly totals, and your streaks.

- **One device per phone,** so a family can each have their own.
- **Tied to a person:** link each phone to a Home Assistant user, and one shared dashboard shows every person their own stats.
- **No YAML.** Everything is set up from the UI. A dhikr you start using appears by itself.
- **Stats only:** no live counting, no location. The phone sends a snapshot after each session, when the app opens, every hour and at midnight.

## Install

[![Open in Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=salihinsaealal&repository=wirid-homeassistant&category=integration)

Settings → Marketplace (or HACS on older Home Assistant) → search **Wirid** → Install → restart Home Assistant.

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
| `today_total`, `today_goal`, `today_goal_percent` | Today and your daily goal (`today_total` carries `color`: today's tier colour as `#RRGGBB`, the cards' colours) | dhikr, % |
| `today_tier` | `emerald` below the goal, then one per lap from the goal on: `gold`, `blue` (`purple` before app 0.11), `pink` (shown as rosé), `silver` (5th lap on) | |
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

Wirid comes with its own dashboard cards. There is nothing else to install: edit a dashboard → **Add card** → search **Wirid**.

| Card | Shows |
|---|---|
| **Wirid today** | Today's ring in the goal-tier colour, %, tier and lap, streak, best, minutes, sessions |
| **Wirid dhikr** | Each dhikr counted today in its app colour, with "Show all" for the rest |
| **Wirid prayer times** | Today's dhikr in each of the nine waktu |
| **Wirid periods** | Last 7 days, this month and this year, with the change |
| **Wirid 14 days** | The last 14 days, stacked by dhikr |
| **Wirid summary** | Active days, the last session and the last sync |
| **Wirid (all)** | All six above in one card |
| **Wirid family** | Every phone's day, one row each, sorted by today's total |

Each one-person card has a **Phone** setting. The default, *Whoever is looking*, shows the phone linked to the person viewing the dashboard (someone with no phone sees nothing), so one shared dashboard works for a whole family. Pick a specific phone instead for a wall tablet or a shared login. The family card lets you choose which phones to show and rename them.

A phone that hasn't synced since midnight is shown faded with "Last synced …", so yesterday's numbers are never mistaken for today's. The 14-day card needs Wirid app 0.4.0 or newer on the phone.

Colours follow the app: emerald below the daily goal, then gold, blue, rosé and silver for each lap from the goal on. On a light theme, coloured text uses darker shades so it stays readable.

### Examples

Everything can be set in the card editor; this is the YAML it writes, if you prefer the code editor.

A personal dashboard that each family member opens on their own phone (everyone sees their own stats):

```yaml
type: vertical-stack
cards:
  - type: custom:wirid-today-card
  - type: custom:wirid-dhikr-card
  - type: custom:wirid-waktu-card
  - type: custom:wirid-periods-card
  - type: custom:wirid-days-card
  - type: custom:wirid-summary-card
```

Or the same in one card:

```yaml
type: custom:wirid-card
```

A kitchen tablet logged in as a shared user: the whole family, plus one person's day pinned below it:

```yaml
type: vertical-stack
cards:
  - type: custom:wirid-family-card
    title: Family today
    phones:            # optional: leave out to show every phone, sorted by today's total
      - prefix: wirid_
        name: Abah
      - prefix: wirid_umi_
        name: Umi
  - type: custom:wirid-today-card
    phone: wirid_umi_  # a fixed phone instead of whoever is looking
```

A phone's prefix is the start of its entity IDs: `wirid_` for the first phone (`sensor.wirid_today_total`), `wirid_<name>_` for later ones. The card editor's dropdowns list the phones by name, so you rarely need to type it.

| Option | Cards | Meaning |
|---|---|---|
| `phone` | all but family | A phone's prefix. Leave out for *whoever is looking*. |
| `title` | family | Heading (default "Family today"). |
| `phones` | family | Which phones, in this order, each with an optional display `name`. |

### Tips

- **Renaming a phone:** Settings → Devices & services → Wirid → the device → ✏️ → Name. When Home Assistant offers to rename the entity IDs too, choose **No**: the IDs keep your history and graphs. The cards pick up the new name by themselves.
- **A card is empty:** in *whoever is looking* mode a card hides itself for someone with no linked phone. Link the phone to that person (the integration's **Configure**), or pick a fixed phone in the card.
- **"Waiting for the first sync":** the phone is added but hasn't sent yet. Open Wirid on the phone with **Send stats to Home Assistant** on.
- **Cards don't show up after an update:** refresh the browser (or clear the app's cache in the Companion app).

### The old YAML cards

`dashboard/wirid-cards.yaml` (button-card templates) still works but is replaced by these cards and will be removed in a later release. To switch, delete those cards from the dashboard and add the Wirid cards above; nothing else changes.

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

Wirid for Android is in a closed test on Google Play: [join here](https://salihinsaealal.github.io/wirid-site/testers.html).

## Licence

MIT
