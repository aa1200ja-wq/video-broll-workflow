from pathlib import Path
from urllib.parse import urlparse
import uuid
import httpx
from fastapi import UploadFile
from app.config import settings
from app.models import MaterialAsset, Project, Scene, SearchResult
from app.services import library
from app.services.projects import save_project


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
    return library.assign_asset(project, scene, asset)


async def download_asset(project: Project, scene: Scene, result: SearchResult) -> Project:
    query = scene.search_query.strip()
    if result.source == "local" or result.download_url.startswith("local://"):
        asset = library.find_asset(result.id)
        if not asset:
            raise FileNotFoundError("本機素材不存在")
        if query:
            asset.search_queries = [*asset.search_queries, query]
            library.upsert_asset(asset)
        return _select(project, scene, asset)

    _validate_remote(result.download_url)
    existing = library.find_asset(result.id)
    if existing and Path(existing.local_path).exists():
        if query:
            existing.search_queries = [*existing.search_queries, query]
        existing.tags = [*existing.tags, *result.tags]
        library.upsert_asset(existing)
        return _select(project, scene, existing)

    target = settings.assets_path / f"{result.id}{_safe_suffix(result.download_url, result.media_type)}"
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
    library.upsert_asset(asset)
    return _select(project, scene, asset)


async def upload_asset(project: Project, scene: Scene, upload: UploadFile) -> Project:
    suffix = Path(upload.filename or "asset").suffix.lower()
    asset_id = f"manual-{uuid.uuid4().hex[:10]}"
    target = settings.assets_path / f"{asset_id}{suffix or '.bin'}"
    target.write_bytes(await upload.read())
    image_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    media_type = "image" if suffix in image_ext else "video"
    asset = MaterialAsset(
        id=asset_id, media_type=media_type, local_path=str(target.resolve()),
        source="manual", title=upload.filename or asset_id,
        search_queries=[scene.search_query] if scene.search_query.strip() else [],
    )
    library.upsert_asset(asset)
    return _select(project, scene, asset)
