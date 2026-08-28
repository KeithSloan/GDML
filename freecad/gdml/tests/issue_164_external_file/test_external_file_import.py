"""Regression test for GDML issue #164 using a real FreeCAD process."""

import os
import subprocess
import unittest
from pathlib import Path


class ExternalFileImportTest(unittest.TestCase):
    def test_external_world_and_parent_context_are_imported(self):
        repository_root = Path(__file__).resolve().parents[4]
        fixture_directory = Path(__file__).resolve().parent
        executable = os.environ.get("FREECAD_EXECUTABLE")
        self.assertTrue(executable, "FREECAD_EXECUTABLE must point to freecadcmd")

        environment = os.environ.copy()
        environment["GDML_REPOSITORY_ROOT"] = str(repository_root)
        environment["GDML_EXTERNAL_FILE_FIXTURES"] = str(fixture_directory)
        result = subprocess.run(
            [executable, str(fixture_directory / "freecad_driver.py")],
            cwd=repository_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        self.assertIn("GDML_EXTERNAL_FILE_IMPORT=COMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()
