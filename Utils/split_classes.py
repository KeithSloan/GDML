#!/usr/bin/env python3
"""
split_classes <filename>

Process a Python source file and create a directory containing
one file per class definition found in the source.

Actions performed:
- Create a backup of the source file in ./backup/
- Create a directory named after the source file (without .py)
- Write each class definition to its own file in that directory
"""

import ast
import shutil
import sys
from pathlib import Path


def split_classes(filename):
    """
    Process a Python file and create a directory of class definitions.

    Parameters
    ----------
    filename : str
        Path to a Python source file (.py)

    Effects
    -------
    - Creates ./backup/<filename>
    - Creates ./<module_name>/
    - Writes one <ClassName>.py file per class definition
    """

    source_file = Path(filename)

    print(f"[INFO] Processing file: {source_file}")

    if not source_file.exists():
        raise FileNotFoundError(f"File not found: {source_file}")

    if source_file.suffix != ".py":
        raise ValueError(f"Not a Python file: {source_file}")

    module_name = source_file.stem

    # ------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)

    backup_file = backup_dir / source_file.name
    shutil.copy2(source_file, backup_file)
    print(f"[INFO] Backup created: {backup_file}")

    # ------------------------------------------------------------
    # Output directory
    # ------------------------------------------------------------
    out_dir = Path(module_name)
    out_dir.mkdir(exist_ok=True)
    print(f"[INFO] Output directory: {out_dir}")

    # ------------------------------------------------------------
    # Parse source
    # ------------------------------------------------------------
    source_text = source_file.read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    # Collect import statements
    imports = [
        node for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]

    import_text = "\n".join(
        ast.get_source_segment(source_text, node) for node in imports
    )

    # ------------------------------------------------------------
    # Split classes
    # ------------------------------------------------------------
    class_count = 0

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            class_src = ast.get_source_segment(source_text, node)

            out_file = out_dir / f"{class_name}.py"

            with out_file.open("w", encoding="utf-8") as f:
                if import_text:
                    f.write(import_text + "\n\n")
                f.write(class_src + "\n")

            print(f"[OK] Wrote class: {out_file}")
            class_count += 1

    if class_count == 0:
        print("[WARN] No class definitions found")
    else:
        print(f"[DONE] {class_count} class files created in '{out_dir}/'")


# -----------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print("  split_classes <filename>")
        print()
        print("Example:")
        print("  split_classes GDMLObjects.py")
        sys.exit(1)

    try:
        split_classes(sys.argv[1])
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

