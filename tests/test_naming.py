from custom_components.wirid.naming import FIXED, dhikr_ids, phone_slug, prefix_for


def test_first_phone_gets_plain_prefix(): assert prefix_for("Salihin's phone", set()) == "wirid_"
def test_second_phone_gets_named_prefix(): assert prefix_for("Aisyah", {"wirid_"}) == "wirid_aisyah_"
def test_prefix_collision(): assert prefix_for("Aisyah", {"wirid_", "wirid_aisyah_"}) == "wirid_aisyah2_"
def test_phone_slug(): assert phone_slug("Salihin's Phone!") == "salihin_s_phone" and phone_slug("ـــ") == "phone"


def test_dhikr_ids(): assert dhikr_ids("subhanallah") == ("subhanallah_today", "subhanallah_all_time")


def test_fixed_ids_match_yaml():
    ids = [i for i, _ in FIXED]
    assert ids[:6] == ["today_total", "today_goal", "today_goal_percent", "today_tier", "today_sessions", "today_minutes"]
    assert "today_tahajjud" in ids and ids[-1] == "last_sent" and len(ids) == 6 + 9 + 6 + 3 + 1 + 1
    assert dict(FIXED)["today_subuh"] == "Today Subuh" and dict(FIXED)["week_change"] == "Week change"
