"""Profile data model and management for ViTouch key bindings."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from vitouch.config import get_config_dir


@dataclass
class KeyBinding:
    """A single key-to-touch binding with clean circular styling."""
    id: str
    key: str               # e.g., "KEY_S", "KEY_D", "KEY_1"
    display_key: str       # e.g., "S", "D", "1", "TAB"
    norm_x: float = 0.5    # Normalized X coordinate (0.0 to 1.0)
    norm_y: float = 0.5    # Normalized Y coordinate (0.0 to 1.0)
    label: str = ""        # Optional internal description
    color: str = "#E2E8F0" # Translucent light-gray glass
    radius: int = 24       # Button radius in pixels
    duration_ms: int = 80  # Touch press duration in milliseconds
    group_id: Optional[str] = None

    def to_pixel_coords(self, screen_width: int, screen_height: int) -> tuple[int, int]:
        px = int(round(self.norm_x * screen_width))
        py = int(round(self.norm_y * screen_height))
        return px, py

    def update_from_pixel_coords(self, px: int, py: int, screen_width: int, screen_height: int) -> None:
        self.norm_x = max(0.0, min(1.0, px / max(screen_width, 1)))
        self.norm_y = max(0.0, min(1.0, py / max(screen_height, 1)))


@dataclass
class KeyGroup:
    """Retained for JSON structure compatibility."""
    id: str = "default"
    name: str = "Tất cả phím"
    trigger_key: str = ""
    binding_ids: List[str] = field(default_factory=list)
    inject_trigger_touch: bool = True
    initial_visible: bool = True


@dataclass
class Resolution:
    width: int = 1366
    height: int = 768


@dataclass
class GameProfile:
    """A complete profile configuration for a game."""
    name: str = "TFT Mobile"
    version: str = "1.4.0"
    description: str = "Cấu hình phím chuẩn TFT Mobile: S = Shop, D = Roll, 1-5 = Mua tướng"
    resolution: Resolution = field(default_factory=Resolution)
    hotkeys: Dict[str, str] = field(default_factory=lambda: {
        "toggle_edit": "KEY_F1",
        "toggle_play": "KEY_F2",
        "toggle_visibility": "KEY_F3"
    })
    tap_duration_ms: int = 120
    groups: List[KeyGroup] = field(default_factory=list)
    bindings: List[KeyBinding] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameProfile":
        res_data = data.get("resolution", {})
        res = Resolution(
            width=res_data.get("width", 1366),
            height=res_data.get("height", 768)
        )
        groups = [
            KeyGroup(**g) for g in data.get("groups", [])
        ]
        bindings = []
        for b in data.get("bindings", []):
            b.pop("type", None)
            b.pop("end_norm_x", None)
            b.pop("end_norm_y", None)
            bindings.append(KeyBinding(**b))

        return cls(
            name=data.get("name", "Unnamed Profile"),
            version=data.get("version", "1.4.0"),
            description=data.get("description", ""),
            resolution=res,
            tap_duration_ms=int(data.get("tap_duration_ms", 120)),
            hotkeys=data.get("hotkeys", {}),
            groups=groups,
            bindings=bindings
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "resolution": asdict(self.resolution),
            "tap_duration_ms": self.tap_duration_ms,
            "hotkeys": self.hotkeys,
            "groups": [asdict(g) for g in self.groups],
            "bindings": [asdict(b) for b in self.bindings]
        }

    def save(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Path) -> "GameProfile":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cls.from_dict(data)


def get_profiles_dir() -> Path:
    path = get_config_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_available_profiles() -> List[str]:
    """Return list of available profile names without .json extension."""
    prof_dir = get_profiles_dir()
    profiles = set()
    if prof_dir.exists():
        for p in prof_dir.glob("*.json"):
            profiles.add(p.stem)

    # Ensure TFT Mobile is always in the list
    if "tft_mobile" not in profiles:
        profiles.add("tft_mobile")

    return sorted(list(profiles))


def load_profile_by_name(name: str) -> GameProfile:
    """Load a profile by its slug/name, or create if default."""
    prof_dir = get_profiles_dir()
    safe_name = name.lower().replace(" ", "_")
    target_path = prof_dir / f"{safe_name}.json"

    if target_path.exists():
        try:
            return GameProfile.load(target_path)
        except Exception as e:
            print(f"[Profile] Error loading profile '{safe_name}': {e}")

    # Fallback / Built-in templates
    if safe_name == "wild_rift":
        prof = GameProfile(
            name="Tốc Chiến (Wild Rift)",
            bindings=[
                KeyBinding(id="btn_atk", key="KEY_SPACE", display_key="SPC", norm_x=0.90, norm_y=0.82),
                KeyBinding(id="btn_s1", key="KEY_Q", display_key="Q", norm_x=0.76, norm_y=0.85),
                KeyBinding(id="btn_s2", key="KEY_W", display_key="W", norm_x=0.80, norm_y=0.70),
                KeyBinding(id="btn_s3", key="KEY_E", display_key="E", norm_x=0.88, norm_y=0.60),
                KeyBinding(id="btn_ult", key="KEY_R", display_key="R", norm_x=0.95, norm_y=0.55),
                KeyBinding(id="btn_f1", key="KEY_D", display_key="D", norm_x=0.70, norm_y=0.70),
                KeyBinding(id="btn_f2", key="KEY_F", display_key="F", norm_x=0.68, norm_y=0.85),
            ]
        )
    elif safe_name == "genshin_impact":
        prof = GameProfile(
            name="Genshin Impact",
            bindings=[
                KeyBinding(id="btn_atk", key="KEY_SPACE", display_key="SPC", norm_x=0.90, norm_y=0.80),
                KeyBinding(id="btn_skill", key="KEY_E", display_key="E", norm_x=0.82, norm_y=0.72),
                KeyBinding(id="btn_burst", key="KEY_Q", display_key="Q", norm_x=0.92, norm_y=0.60),
                KeyBinding(id="btn_jump", key="KEY_F", display_key="F", norm_x=0.95, norm_y=0.90),
                KeyBinding(id="btn_c1", key="KEY_1", display_key="1", norm_x=0.96, norm_y=0.25),
                KeyBinding(id="btn_c2", key="KEY_2", display_key="2", norm_x=0.96, norm_y=0.33),
                KeyBinding(id="btn_c3", key="KEY_3", display_key="3", norm_x=0.96, norm_y=0.41),
                KeyBinding(id="btn_c4", key="KEY_4", display_key="4", norm_x=0.96, norm_y=0.49),
            ]
        )
    else:
        # Default TFT Mobile
        prof = GameProfile(
            name="TFT Mobile",
            bindings=[
                KeyBinding(id="btn_xp", key="KEY_E", display_key="E", norm_x=0.12, norm_y=0.91),
                KeyBinding(id="btn_reroll", key="KEY_D", display_key="D", norm_x=0.22, norm_y=0.91),
                KeyBinding(id="btn_lock", key="KEY_TAB", display_key="TAB", norm_x=0.05, norm_y=0.91),
                KeyBinding(id="btn_shop_1", key="KEY_1", display_key="1", norm_x=0.32, norm_y=0.88),
                KeyBinding(id="btn_shop_2", key="KEY_2", display_key="2", norm_x=0.44, norm_y=0.88),
                KeyBinding(id="btn_shop_3", key="KEY_3", display_key="3", norm_x=0.56, norm_y=0.88),
                KeyBinding(id="btn_shop_4", key="KEY_4", display_key="4", norm_x=0.68, norm_y=0.88),
                KeyBinding(id="btn_shop_5", key="KEY_5", display_key="5", norm_x=0.80, norm_y=0.88),
                KeyBinding(id="btn_sell", key="KEY_W", display_key="W", norm_x=0.50, norm_y=0.96),
                KeyBinding(id="btn_toggle_shop", key="KEY_S", display_key="S", norm_x=0.93, norm_y=0.91),
                KeyBinding(id="btn_scout_next", key="KEY_R", display_key="R", norm_x=0.96, norm_y=0.50),
            ]
        )

    prof.save(target_path)
    return prof


def create_new_custom_profile(profile_name: str) -> GameProfile:
    """Create a new empty profile with given name."""
    safe_name = profile_name.strip().lower().replace(" ", "_")
    prof = GameProfile(
        name=profile_name.strip() or "Custom Game",
        bindings=[]
    )
    target_path = get_profiles_dir() / f"{safe_name}.json"
    prof.save(target_path)
    return prof


def load_or_init_default_profile(builtin_profiles_dir: Optional[Path] = None) -> GameProfile:
    return load_profile_by_name("tft_mobile")
