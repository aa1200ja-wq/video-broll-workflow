import json
from pathlib import Path
from app.config import settings
from app.models import MaterialAsset, Project, Scene, SearchResult
from app.services.projects import list_projects, save_project


def load_library() -> list[MaterialAsset]:
    _migrate_legacy()
    path = settings.library_path
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [MaterialAsset.model_validate(item) for item in raw]
    except (ValueError, json.JSONDecodeError):
        return []


def save_library(items: list[MaterialAsset]) -> list[MaterialAsset]:
    path = settings.library_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [item.model_dump(exclude={"used_by"}) for item in items]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def find_asset(asset_id: str) -> MaterialAsset | None:
    return next((x for x in load_library() if x.id == asset_id), None)


def upsert_asset(asset: MaterialAsset) -> MaterialAsset:
    items = load_library()
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
    save_library(items)
    return asset


def list_library(query: str = "") -> list[MaterialAsset]:
    items = load_library()
    usage = _usage_map()
    for item in items:
        item.used_by = usage.get(str(Path(item.local_path)), [])
    if not query.strip():
        return items
    ranked = _ranked(items, query)
    return [item for _, item in ranked]


def search_results(query: str, limit: int = 12) -> list[SearchResult]:
    ranked = _ranked(load_library(), query)[:limit]
    return [
        SearchResult(
            id=item.id, source="local", media_type=item.media_type,
            preview_url=f"/api/library/{item.id}/file",
            download_url=f"local://{item.id}", page_url=item.source_url,
            author=item.author, title=item.title, tags=item.tags,
        )
        for _, item in ranked
        if Path(item.local_path).exists()
    ]


def assign_asset(project: Project, scene: Scene, asset: MaterialAsset) -> Project:
    if not Path(asset.local_path).exists():
        raise FileNotFoundError("素材檔案不存在")
    scene.selected_asset = asset.local_path
    scene.selected_asset_type = asset.media_type
    scene.source_name = asset.source
    scene.source_url = asset.source_url or None
    scene.status = "asset_selected"
    return save_project(project)


def _ranked(items: list[MaterialAsset], query: str):
    words = [x for x in query.lower().replace(",", " ").split() if x]
    phrase = query.strip().lower()
    ranked = []
    for item in items:
        text = _search_text(item)
        score = (100 if phrase and phrase in text else 0)
        score += sum(10 for word in words if word in text)
        if score:
            ranked.append((score, item))
    return sorted(ranked, key=lambda pair: pair[0], reverse=True)


def _usage_map() -> dict[str, list[str]]:
    usage: dict[str, list[str]] = {}
    for project in list_projects():
        for scene in project.scenes:
            if scene.selected_asset:
                key = str(Path(scene.selected_asset))
                usage.setdefault(key, []).append(f"{project.name} / {scene.id}")
    return usage


def _search_text(asset: MaterialAsset) -> str:
    parts = [
        asset.id, asset.source, asset.author, asset.title,
        *asset.tags, *asset.search_queries,
    ]
    return " ".join(parts).lower()


def _merge(left: list[str], right: list[str]) -> list[str]:
    result, seen = [], set()
    for value in [*left, *right]:
        clean = value.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _migrate_legacy() -> None:
    if settings.library_path.exists():
        return
    merged: list[MaterialAsset] = []
    for path in settings.projects_path.glob("*/library.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            merged.extend(MaterialAsset.model_validate(x) for x in raw)
        except (ValueError, json.JSONDecodeError):
            continue
    if not merged:
        return
    deduped: dict[str, MaterialAsset] = {}
    for item in merged:
        if item.id not in deduped:
            deduped[item.id] = item
        else:
            old = deduped[item.id]
            old.tags = _merge(old.tags, item.tags)
            old.search_queries = _merge(old.search_queries, item.search_queries)
    save_library(list(deduped.values()))
