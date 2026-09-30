from pathlib import Path
from urllib.parse import urlparse
import httpx
from fastapi import UploadFile
from app.models import Project, Scene, SearchResult
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


async def download_asset(project: Project, scene: Scene, result: SearchResult) -> Project:
    _validate_remote(result.download_url)
    folder = project_path(project.id) / "assets" / scene.id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{result.id}{_safe_suffix(result.download_url, result.media_type)}"
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        async with client.stream("GET", result.download_url) as response:
            response.raise_for_status()
            with target.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    scene.selected_asset = str(target.resolve())
    scene.selected_asset_type = result.media_type
    scene.source_name = result.source
    scene.source_url = result.page_url
    scene.status = "asset_selected"
    return save_project(project)


async def upload_asset(project: Project, scene: Scene, upload: UploadFile) -> Project:
    folder = project_path(project.id) / "assets" / scene.id
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "asset").suffix.lower()
    target = folder / f"manual{suffix or '.bin'}"
    target.write_bytes(await upload.read())
    image_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    scene.selected_asset = str(target.resolve())
    scene.selected_asset_type = "image" if suffix in image_ext else "video"
    scene.source_name = "manual"
    scene.source_url = None
    scene.status = "asset_selected"
    return save_project(project)
