"""Unit tests for ViTouch profile serialization."""

import unittest
import tempfile
from pathlib import Path

from vitouch.profile import GameProfile, KeyBinding, Resolution


class TestProfile(unittest.TestCase):

    def test_keybinding_coordinates(self):
        binding = KeyBinding(
            id="test_btn",
            key="KEY_E",
            display_key="E",
            norm_x=0.5,
            norm_y=0.25
        )

        px, py = binding.to_pixel_coords(1366, 768)
        self.assertEqual(px, 683)
        self.assertEqual(py, 192)

        binding.update_from_pixel_coords(1366, 768, 1366, 768)
        self.assertEqual(binding.norm_x, 1.0)
        self.assertEqual(binding.norm_y, 1.0)

    def test_profile_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            prof = GameProfile(
                name="Test Profile",
                resolution=Resolution(width=1366, height=768),
                bindings=[
                    KeyBinding(id="b_shop1", key="KEY_1", display_key="1", norm_x=0.3, norm_y=0.8),
                    KeyBinding(id="b_xp", key="KEY_E", display_key="E", norm_x=0.12, norm_y=0.91)
                ]
            )

            file_path = Path(tmp_dir) / "test_prof.json"
            prof.save(file_path)
            self.assertTrue(file_path.exists())

            loaded = GameProfile.load(file_path)
            self.assertEqual(loaded.name, "Test Profile")
            self.assertEqual(len(loaded.bindings), 2)
            self.assertEqual(loaded.bindings[0].display_key, "1")
            self.assertEqual(loaded.bindings[1].key, "KEY_E")


if __name__ == "__main__":
    unittest.main()
