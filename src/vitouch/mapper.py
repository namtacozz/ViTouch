"""Key-to-Touch mapping engine for ViTouch."""

from typing import Callable, Dict, Optional
from vitouch.profile import GameProfile, KeyBinding
from vitouch.touch_inject import TouchInjector


class MappingEngine:
    """Orchestrates keyboard inputs into touch events and visual feedback."""

    def __init__(self, profile: GameProfile, touch_injector: TouchInjector):
        self.profile = profile
        self.touch_injector = touch_injector
        self.enabled = True
        self.edit_mode = False
        self.overlay_visible = True

        # Lookup structure
        self._key_map: Dict[str, KeyBinding] = {}
        self._rebuild_lookup()

        # Callbacks for UI updates
        self.on_key_activated: Optional[Callable[[str], None]] = None
        self.on_mode_changed: Optional[Callable[[str], None]] = None
        self.on_visibility_changed: Optional[Callable[[bool], None]] = None
        self.on_rebind_key: Optional[Callable[[str], None]] = None

    def _rebuild_lookup(self) -> None:
        self._key_map.clear()
        for binding in self.profile.bindings:
            self._key_map[binding.key] = binding

    def set_profile(self, profile: GameProfile) -> None:
        """Update active profile."""
        self.profile = profile
        self._rebuild_lookup()

    def handle_key_down(self, key_name: str) -> None:
        """Process key down event."""
        # 1. System control hotkeys
        hotkeys = self.profile.hotkeys
        if key_name == hotkeys.get("toggle_edit", "KEY_F1"):
            self.toggle_edit_mode()
            return
        elif key_name == hotkeys.get("toggle_play", "KEY_F2"):
            self.set_play_mode()
            return
        elif key_name == hotkeys.get("toggle_visibility", "KEY_F3"):
            self.toggle_visibility()
            return

        # If in edit mode, forward key to in-place rebind if active
        if self.edit_mode:
            if self.on_rebind_key:
                try:
                    self.on_rebind_key(key_name)
                except Exception:
                    pass
            return

        if not self.enabled:
            return

        # 2. Check game keybinding
        binding = self._key_map.get(key_name)
        if not binding:
            return

        # Visual activation pulse
        if self.on_key_activated:
            try:
                self.on_key_activated(binding.id)
            except Exception:
                pass

        # 3. Inject touch event
        px, py = binding.to_pixel_coords(
            self.profile.resolution.width,
            self.profile.resolution.height
        )
        duration = self.profile.tap_duration_ms if hasattr(self.profile, "tap_duration_ms") and self.profile.tap_duration_ms else max(120, binding.duration_ms)
        self.touch_injector.tap(px, py, duration_ms=duration)

    def handle_key_up(self, key_name: str) -> None:
        """Process key up event."""
        pass

    def toggle_edit_mode(self) -> None:
        """Switch between Edit Mode and Play Mode."""
        self.edit_mode = not self.edit_mode
        mode_str = "edit" if self.edit_mode else "play"
        print(f"[Engine] Mode switched to: {mode_str.upper()}")
        if self.on_mode_changed:
            self.on_mode_changed(mode_str)

    def set_play_mode(self) -> None:
        """Explicitly switch to Play Mode."""
        if self.edit_mode:
            self.edit_mode = False
            if self.on_mode_changed:
                self.on_mode_changed("play")

    def toggle_visibility(self) -> None:
        """Toggle overlay window visibility."""
        self.overlay_visible = not self.overlay_visible
        if self.on_visibility_changed:
            self.on_visibility_changed(self.overlay_visible)
