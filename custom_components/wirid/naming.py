"""Entity naming rules (pure, no Home Assistant)."""

from __future__ import annotations

import re
import unicodedata

from .const import WAKTU, WAKTU_NAMES


def phone_slug(name: str) -> str:
    """Lowercase ASCII slug of a phone name; "phone" when nothing is left."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    return slug or "phone"


def prefix_for(phone_name: str, taken: set[str]) -> str:
    """Entity-id prefix: plain "wirid_" for the first phone, then a named one."""
    if "wirid_" not in taken:
        return "wirid_"
    base = f"wirid_{phone_slug(phone_name)}"
    candidate, n = f"{base}_", 1
    while candidate in taken:
        n += 1
        candidate = f"{base}{n}_"
    return candidate


FIXED: tuple[tuple[str, str], ...] = (
    ("today_total", "Today total"),
    ("today_goal", "Today goal"),
    ("today_goal_percent", "Today goal percent"),
    ("today_tier", "Today tier"),
    ("today_sessions", "Today sessions"),
    ("today_minutes", "Today minutes"),
    *((f"today_{w}", f"Today {WAKTU_NAMES[w]}") for w in WAKTU),
    ("week_total", "Week total"),
    ("week_change", "Week change"),
    ("month_total", "Month total"),
    ("month_change", "Month change"),
    ("year_total", "Year total"),
    ("year_change", "Year change"),
    ("streak_current", "Streak current"),
    ("streak_best", "Streak best"),
    ("active_days", "Active days"),
    ("last_session", "Last session"),
    ("last_sent", "Last sent"),
)


def dhikr_ids(slug: str) -> tuple[str, str]:
    """Object ids of a dhikr's two sensors."""
    return f"{slug}_today", f"{slug}_all_time"
