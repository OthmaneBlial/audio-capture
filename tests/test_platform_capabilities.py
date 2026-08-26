import tempfile
import unittest
from pathlib import Path

from platform_capabilities import detect_desktop_capabilities


class PlatformCapabilityTests(unittest.TestCase):
    def test_wayland_disables_tray_and_global_shortcut_with_explanation(self):
        with tempfile.TemporaryDirectory() as directory:
            capabilities = detect_desktop_capabilities(
                {"XDG_SESSION_TYPE": "wayland"}, flatpak_info=Path(directory) / "missing"
            )
        self.assertTrue(capabilities.focused_push_to_talk)
        self.assertFalse(capabilities.tray_window_toggle)
        self.assertFalse(capabilities.global_shortcut)
        self.assertIn("Wayland", capabilities.explanation)

    def test_unsandboxed_x11_enables_only_legacy_tray_toggle(self):
        with tempfile.TemporaryDirectory() as directory:
            capabilities = detect_desktop_capabilities(
                {"XDG_SESSION_TYPE": "x11"}, flatpak_info=Path(directory) / "missing"
            )
        self.assertTrue(capabilities.tray_window_toggle)
        self.assertFalse(capabilities.global_shortcut)

    def test_flatpak_disables_legacy_tray(self):
        with tempfile.TemporaryDirectory() as directory:
            info = Path(directory) / ".flatpak-info"
            info.touch()
            capabilities = detect_desktop_capabilities(
                {"XDG_SESSION_TYPE": "x11"}, flatpak_info=info
            )
        self.assertTrue(capabilities.sandboxed)
        self.assertFalse(capabilities.tray_window_toggle)


if __name__ == "__main__":
    unittest.main()
