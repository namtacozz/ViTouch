"""Configuration management for ViTouch."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


def get_config_dir() -> Path:
    """Get the user's config directory (~/.config/vitouch)."""
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    path = Path(base) / "vitouch"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class AppConfig:
    """Global configuration settings for ViTouch."""
    active_profile: str = "tft_mobile"
    default_width: int = 1366
    default_height: int = 768
    overlay_opacity_play: float = 0.65
    overlay_opacity_edit: float = 0.95
    show_labels_in_play_mode: bool = True
    keyboard_device_path: str = ""  # auto-detected if empty
    touch_duration_ms: int = 35
    custom_profiles_dir: str = ""
    hotkey_edit_mode: str = "KEY_F1"
    hotkey_play_mode: str = "KEY_F2"
    hotkey_toggle_overlay: str = "KEY_F3"

    @classmethod
    def load(cls) -> "AppConfig":
        cfg_file = get_config_dir() / "config.json"
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        cfg_file = get_config_dir() / "config.json"
        try:
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")
