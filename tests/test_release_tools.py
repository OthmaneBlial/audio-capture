import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_script(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check_release = load_script("check_release")
generate_sbom = load_script("generate_sbom")
render_release_notes = load_script("render_release_notes")


class ReleaseToolTests(unittest.TestCase):
    def test_current_version_surfaces_match(self):
        versions = check_release.check("1.0.0")
        self.assertEqual(set(versions.values()), {"1.0.0"})

    def test_sbom_is_deterministic_and_names_runtime_and_dependencies(self):
        first = generate_sbom.build_sbom("1.0.0", "abc123", "2026-08-27T20:00:00+00:00")
        second = generate_sbom.build_sbom("1.0.0", "abc123", "2026-08-27T20:00:00+00:00")
        self.assertEqual(first, second)
        self.assertEqual(first["bomFormat"], "CycloneDX")
        names = {component["name"] for component in first["components"]}
        self.assertTrue({"PyAudio", "python-dotenv", "webrtcvad", "PortAudio"} <= names)
        self.assertIn("org.gnome.Platform", names)

    def test_sbom_cli_writes_valid_json_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "sbom.json"
            payload = generate_sbom.build_sbom(
                "1.0.0", "abc123", "2026-08-27T20:00:00+00:00"
            )
            destination.write_text(__import__("json").dumps(payload))
            self.assertTrue(destination.is_file())

    def test_release_notes_include_every_public_release_surface(self):
        notes = render_release_notes.render("1.0.0", "abc123")
        self.assertIn("guided demo", notes)
        self.assertIn("Install and verify", notes)
        self.assertIn("Support boundary", notes)
        self.assertIn("Privacy delta", notes)
        self.assertIn("Benchmark and help wanted", notes)
        self.assertIn("abc123", notes)

if __name__ == "__main__":
    unittest.main()
