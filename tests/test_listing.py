"""Checks for the HACS / Marketplace catalog listing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMP = ROOT / "custom_components" / "wirid"
BADGE = (
    "https://my.home-assistant.io/redirect/hacs_repository/"
    "?owner=salihinsaealal&repository=wirid-homeassistant&category=integration"
)
TESTERS = "https://salihinsaealal.github.io/wirid-site/testers.html"


def _manifest():
    return json.loads((COMP / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_category():
    assert _manifest()["categories"] == ["health_wellbeing"]


def test_manifest_version():
    assert _manifest()["version"] == "0.2.1"


def test_translations_only():
    assert not (COMP / "strings.json").exists()
    assert (COMP / "translations" / "en.json").exists()
    assert (COMP / "translations" / "ms.json").exists()


def test_readme_listing():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert BADGE in readme
    assert "search **Wirid**" in readme
    assert TESTERS in readme
    assert "coming soon" not in readme


def test_manifest_key_order():
    keys = list(_manifest())
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])
