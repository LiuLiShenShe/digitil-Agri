"""Batch convert OBJ+MTL → GLB and place in import directories."""
import os
import sys
import shutil
from pathlib import Path

import trimesh

ASSERTS = Path("/data/fj/数字孪生/asserts")
IMPORT = Path("/data/fj/数字孪生/digital-twingo/scene-server-go/scene-assets/import")

# Mapping: source dir → target category dir
CONVERSIONS = [
    ("Farm Buildings Pack OBJ", "building"),
    ("nature crop pack OBJ", "plant"),
    ("Ultimate Nature Pack OBJ", "plant"),
]

def convert_obj_to_glb(obj_path: Path, out_path: Path) -> bool:
    """Convert a single OBJ+MTL to GLB using trimesh, preserving materials."""
    try:
        # Load with materials (no force="mesh" so MTL colors are preserved)
        scene_or_mesh = trimesh.load(str(obj_path))
        if isinstance(scene_or_mesh, trimesh.Scene):
            # Keep scene structure to preserve materials
            # Export scene directly (supports materials)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            scene_or_mesh.export(str(out_path), file_type="glb")
            size_kb = out_path.stat().st_size / 1024
            print(f"  → {out_path.name} ({size_kb:.0f} KB) [scene, {len(scene_or_mesh.geometry)} parts]")
            return True

        # Single mesh
        mesh = scene_or_mesh
        if mesh.vertices.shape[0] == 0:
            print(f"  SKIP: empty mesh")
            return False

        out_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(str(out_path), file_type="glb")
        size_kb = out_path.stat().st_size / 1024
        print(f"  → {out_path.name} ({size_kb:.0f} KB)")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    total = 0
    for src_dir, category in CONVERSIONS:
        src = ASSERTS / src_dir
        if not src.exists():
            print(f"SKIP: {src} not found")
            continue

        dest = IMPORT / category
        dest.mkdir(parents=True, exist_ok=True)

        obj_files = list(src.glob("*.obj"))
        print(f"\n{'='*60}")
        print(f"{src_dir}: {len(obj_files)} OBJ files → category '{category}'")
        print(f"{'='*60}")

        for obj_file in sorted(obj_files):
            name = obj_file.stem  # filename without extension
            glb_file = dest / f"{name}.glb"

            if glb_file.exists():
                print(f"  SKIP: {name}.glb already exists")
                continue

            print(f"  Converting: {obj_file.name}")
            if convert_obj_to_glb(obj_file, glb_file):
                total += 1

    print(f"\n{'='*60}")
    print(f"Done! Converted {total} models.")
    print(f"Import dir: {IMPORT}")
    for d in sorted(IMPORT.iterdir()):
        if d.is_dir():
            count = len(list(d.glob("*.glb")))
            print(f"  {d.name}/ : {count} GLBs")


if __name__ == "__main__":
    main()
