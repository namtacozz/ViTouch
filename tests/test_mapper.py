"""Unit tests for ViTouch MappingEngine."""

import unittest
from unittest.mock import MagicMock
from vitouch.mapper import MappingEngine
from vitouch.profile import GameProfile, KeyBinding, Resolution
from vitouch.touch_inject import TouchInjector


class TestMapper(unittest.TestCase):

    def test_mapping_engine_triggers_tap(self):
        prof = GameProfile(
            name="TFT",
            resolution=Resolution(width=1366, height=768),
            bindings=[
                KeyBinding(id="b_xp", key="KEY_E", display_key="E", norm_x=0.12, norm_y=0.91, duration_ms=60)
            ]
        )

        mock_injector = MagicMock(spec=TouchInjector)
        mock_injector.screen_width = 1366
        mock_injector.screen_height = 768
        engine = MappingEngine(profile=prof, touch_injector=mock_injector)

        # Simulate pressing KEY_E
        engine.handle_key_down("KEY_E")

        # Verify mock_injector.tap was called with correct pixel coordinates and min 80ms duration
        expected_x = int(round(0.12 * 1366))
        expected_y = int(round(0.91 * 768))
        mock_injector.tap.assert_called_once_with(expected_x, expected_y, duration_ms=120)

    def test_rebind_callback_in_edit_mode(self):
        prof = GameProfile(
            name="TFT",
            resolution=Resolution(width=1366, height=768),
            bindings=[
                KeyBinding(id="b_xp", key="KEY_E", display_key="E", norm_x=0.12, norm_y=0.91)
            ]
        )

        mock_injector = MagicMock(spec=TouchInjector)
        engine = MappingEngine(profile=prof, touch_injector=mock_injector)
        engine.edit_mode = True

        rebind_callback = MagicMock()
        engine.on_rebind_key = rebind_callback

        # When in edit mode, key down triggers rebind callback instead of touch tap
        engine.handle_key_down("KEY_SPACE")
        rebind_callback.assert_called_once_with("KEY_SPACE")
        self.assertEqual(mock_injector.tap.call_count, 0)


if __name__ == "__main__":
    unittest.main()
