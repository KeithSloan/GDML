"""Integration test for GDML issue #182 using a real FreeCAD process."""

import os
import subprocess
import unittest
from pathlib import Path


class SetMaterialTest(unittest.TestCase):
    def test_set_material_on_volume_changes_exported_solid(self):
        repository_root = Path(__file__).resolve().parents[4]
        driver = Path(__file__).resolve().parent / "freecad_driver.py"
        executable = os.environ.get("FREECAD_EXECUTABLE")
        self.assertTrue(executable, "FREECAD_EXECUTABLE must point to freecadcmd")

        environment = os.environ.copy()
        environment["GDML_REPOSITORY_ROOT"] = str(repository_root)
        result = subprocess.run(
            [executable, str(driver)],
            cwd=repository_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        message = f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=message)
        self.assertIn("GDML_SET_MATERIAL_182=COMPLETE", result.stdout, msg=message)


if __name__ == "__main__":
    unittest.main()
