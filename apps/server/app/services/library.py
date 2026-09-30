import json
from pathlib import Path
from app.models import MaterialAsset, Project, Scene
from app.services.projects import project_path, save_project


def _library_path(project_id: str) -> Path:
    return project_path(project_id) / "library.json"


def load_library(project_id: str) -> list[MaterialAsset]:
    path = _library_path(project_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [MaterialAsset.model_validate(item) for item in raw]
    except (ValueError, json.JSONDecodeError):
        return []


def save_library(project_id: str, items: list[MaterialAsset]) -> list[MaterialAsset]:
    path = _library_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [item.model_dump(exclude={"used_by"}) for item in items]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def find_asset(project_id: str, asset_id: str) -> MaterialAsset | None:
    return next((x for x in load_library(project_id) if x.id == asset_id), None)


def upsert_asset(project_id: str, asset: MaterialAsset) -> MaterialAsset:
    items = load_library(project_id)
    old = next((x for x in items if x.id == asset.id), None)
    if old:
        old.local_path = asset.local_path
        old.source_url = asset.source_url or old.source_url
        old.author = asset.author or old.author
        old.title = asset.title or old.title
        old.tags = _merge(old.tags, asset.tags)
        old.search_queries = _merge(old.search_queries, asset.search_queries)
        asset = old
    else:
        items.append(asset)
    save_library(project_id, items)
    return asset


def list_library(project: Project, query: str = "") -> list[MaterialAsset]:
    items = load_library(project.id)
    q = query.strip().lower()
    for item in items:
        item.used_by = [
            scene.id for scene in project.scenes
            if scene.selected_asset and Path(scene.selected_asset) == Path(item.local_path)
        ]
    if not q:
        return items
    return [item for item in items if q in _search_text(item)]


def assign_asset(project: Project, scene: Scene, asset: MaterialAsset) -> Project:
    if not Path(asset.local_path).exists():
        raise FileNotFoundError("素材檔案不存在")
    scene.selected_asset = asset.local_path
    scene.selected_asset_type = asset.media_type
    scene.source_name = asset.source
    scene.source_url = asset.source_url or None
    scene.status = "asset_selected"
    return save_project(project)


def _search_text(asset: MaterialAsset) -> str:
    parts = [
        asset.id, asset.source, asset.author, asset.title,
        *asset.tags, *asset.search_queries,
    ]
    return " ".join(parts).lower()


def _merge(left: list[str], right: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in [*left, *right]:
        clean = value.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result
