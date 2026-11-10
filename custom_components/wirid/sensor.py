"""Wirid sensors: fixed stats plus a today/all-time pair per dhikr."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_PREFIX, CONF_USER_ID, DOMAIN, WAKTU, signal_update
from .entity import WiridEntity
from .naming import FIXED, dhikr_ids
from .payload import Dhikr, Snapshot

DHIKR, PERCENT, SESSIONS, MIN, DAYS = "dhikr", "%", "sessions", "min", "days"


@dataclass(frozen=True)
class Spec:
    value: Callable[[Snapshot], object]
    unit: str | None = None
    measurement: bool = True


SPECS: dict[str, Spec] = {
    "today_total": Spec(lambda s: s.today_total, DHIKR),
    "today_goal": Spec(lambda s: s.goal, DHIKR),
    "today_goal_percent": Spec(lambda s: s.goal_percent, PERCENT),
    "today_tier": Spec(lambda s: s.tier, None, False),
    "today_sessions": Spec(lambda s: s.sessions, SESSIONS),
    "today_minutes": Spec(lambda s: s.minutes, MIN),
    **{f"today_{w}": Spec(lambda s, w=w: s.waktu.get(w, 0), DHIKR) for w in WAKTU},
    "week_total": Spec(lambda s: s.week.total, DHIKR),
    "week_change": Spec(lambda s: s.week.change, PERCENT),
    "month_total": Spec(lambda s: s.month.total, DHIKR),
    "month_change": Spec(lambda s: s.month.change, PERCENT),
    "year_total": Spec(lambda s: s.year.total, DHIKR),
    "year_change": Spec(lambda s: s.year.change, PERCENT),
    "streak_current": Spec(lambda s: s.streak_current, DAYS),
    "streak_best": Spec(lambda s: s.streak_best, DAYS),
    "active_days": Spec(lambda s: s.active_days, DAYS),
    "last_session": Spec(lambda s: s.last_session.count if s.last_session else None, DHIKR),
}


class FixedSensor(WiridEntity, SensorEntity):
    """One of the fixed stats."""

    def __init__(self, entry, object_id: str, name: str) -> None:
        super().__init__(entry, object_id, name)
        self._object_id = object_id
        if object_id == "last_sent":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        else:
            spec = SPECS[object_id]
            self._attr_native_unit_of_measurement = spec.unit
            if spec.measurement:
                self._attr_state_class = SensorStateClass.MEASUREMENT

    def _update_from_snapshot(self) -> None:
        snap = self.snapshot
        oid = self._object_id
        self._attr_extra_state_attributes = {}
        if snap is None:
            self._attr_native_value = None
            self._attr_available = True
            return
        if oid == "last_sent":
            self._attr_native_value = dt_util.parse_datetime(snap.sent) if snap.sent else None
            self._attr_available = True
            self._attr_extra_state_attributes = {
                "wirid_user_id": self._entry.data.get(CONF_USER_ID),
                "wirid_prefix": self._entry.data[CONF_PREFIX],
                "payload_version": snap.version,
                "app_version": snap.app,
            }
            return
        value = SPECS[oid].value(snap)
        self._attr_native_value = value
        self._attr_available = value is not None
        if oid == "last_session" and snap.last_session:
            self._attr_extra_state_attributes = {
                "routine": snap.last_session.routine, "ended": snap.last_session.ended,
            }


class DhikrSensor(WiridEntity, SensorEntity):
    """A dhikr's count today or all time; remembers its last known values."""

    _attr_native_unit_of_measurement = DHIKR

    def __init__(self, entry, dhikr: Dhikr, all_time: bool) -> None:
        today_id, all_id = dhikr_ids(dhikr.slug)
        super().__init__(entry, all_id if all_time else today_id, "")
        self._slug = dhikr.slug
        self._all_time = all_time
        self._last = dhikr
        self._attr_state_class = SensorStateClass.TOTAL if all_time else SensorStateClass.MEASUREMENT

    def _update_from_snapshot(self) -> None:
        snap = self.snapshot
        current = next((d for d in snap.dhikr if d.slug == self._slug), None) if snap else None
        if current is not None:
            self._last = current
        d = self._last
        self._attr_name = f"{d.name} {'all time' if self._all_time else 'today'}"
        if self._all_time:
            self._attr_native_value = d.all_time
        else:
            self._attr_native_value = current.today if current is not None else 0
            self._attr_extra_state_attributes = {
                "color": d.color,
                "mono": d.mono,
                "slug": d.slug,
                "wirid_prefix": self._entry.data[CONF_PREFIX],
            }


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Add the fixed sensors, the stored snapshot's dhikr, and any dhikr that arrives later."""
    seen: set[str] = set()
    async_add_entities([FixedSensor(entry, oid, name) for oid, name in FIXED])

    @callback
    def add_new_dhikr() -> None:
        snap = entry.runtime_data.snapshot
        if snap is None:
            return
        new = [d for d in snap.dhikr if d.slug not in seen]
        seen.update(d.slug for d in new)
        async_add_entities([DhikrSensor(entry, d, a) for d in new for a in (False, True)])

    @callback
    def on_update() -> None:
        add_new_dhikr()
        snap = entry.runtime_data.snapshot
        device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})
        if snap and device and device.sw_version != snap.app:
            dr.async_get(hass).async_update_device(device.id, sw_version=snap.app)

    add_new_dhikr()
    entry.async_on_unload(async_dispatcher_connect(hass, signal_update(entry.entry_id), on_update))
