from pathlib import Path
from urllib.parse import urlparse
import uuid
import httpx
from fastapi import UploadFile
from app.models import MaterialAsset, Project, Scene, SearchResult
from app.services import library
from app.services.projects import project_path, save_project


_ALLOWED_HOST_BITS = ("pexels.com", "pixabay.com", "wikimedia.org", "wikimediausercontent.com")


def _safe_suffix(url: str, media_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix and len(suffix) <= 6:
        return suffix
    return ".mp4" if media_type == "video" else ".jpg"


def _validate_remote(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if not any(bit in host for bit in _ALLOWED_HOST_BITS):
        raise ValueError(f"不允許下載此網域：{host}")


def _select(project: Project, scene: Scene, asset: MaterialAsset) -> Project:
    scene.selected_asset = asset.local_path
    scene.selected_asset_type = asset.media_type
    scene.source_name = asset.source
    scene.source_url = asset.source_url or None
    scene.status = "asset_selected"
    return save_project(project)


async def download_asset(project: Project, scene: Scene, result: SearchResult) -> Project:
    _validate_remote(result.download_url)
    existing = library.find_asset(project.id, result.id)
    query = scene.search_query.strip()
    if existing and Path(existing.local_path).exists():
        existing.search_queries = [*existing.search_queries, query] if query else existing.search_queries
        existing.tags = [*existing.tags, *result.tags]
        library.upsert_asset(project.id, existing)
        return _select(project, scene, existing)

    folder = project_path(project.id) / "assets"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{result.id}{_safe_suffix(result.download_url, result.media_type)}"
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        async with client.stream("GET", result.download_url) as response:
            response.raise_for_status()
            with target.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

    asset = MaterialAsset(
        id=result.id, media_type=result.media_type,
        local_path=str(target.resolve()), source=result.source,
        source_url=result.page_url, author=result.author, title=result.title,
        tags=result.tags, search_queries=[query] if query else [],
    )
    library.upsert_asset(project.id, asset)
    return _select(project, scene, asset)


async def upload_asset(project: Project, scene: Scene, upload: UploadFile) -> Project:
    folder = project_path(project.id) / "assets"
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "asset").suffix.lower()
    asset_id = f"manual-{uuid.uuid4().hex[:10]}"
    target = folder / f"{asset_id}{suffix or '.bin'}"
    target.write_bytes(await upload.read())
    image_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    media_type = "image" if suffix in image_ext else "video"
    asset = MaterialAsset(
        id=asset_id, media_type=media_type, local_path=str(target.resolve()),
        source="manual", title=upload.filename or asset_id,
        search_queries=[scene.search_query] if scene.search_query.strip() else [],
    )
    library.upsert_asset(project.id, asset)
    return _select(project, scene, asset)
