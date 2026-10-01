import json
import shutil
from pathlib import Path
from app.config import settings
from app.services import library


def migrate_material_library(target_dir: str) -> str:
    target_root = Path(target_dir).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    current_root = settings.material_library_path

    if target_root == current_root:
        return str(target_root)

    items = library.load_library()
    target_assets = target_root / "assets"
    target_assets.mkdir(parents=True, exist_ok=True)

    for item in items:
        source = Path(item.local_path)
        if not source.exists():
            continue
        suffix = source.suffix.lower() or (".mp4" if item.media_type == "video" else ".jpg")
        target = target_assets / f"{item.id}{suffix}"
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        item.local_path = str(target.resolve())

    index_path = target_root / "library.json"
    payload = [item.model_dump(exclude={"used_by"}) for item in items]
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return str(target_root)
