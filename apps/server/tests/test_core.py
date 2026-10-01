import json
import os
import tempfile
from pathlib import Path

_temp_root = tempfile.mkdtemp(prefix="broll-tests-")
os.environ["BROLL_DATA_DIR"] = _temp_root
os.environ["PROJECTS_DIR"] = str(Path(_temp_root) / "projects")

from app.config import settings
from app.models import MaterialAsset, Project, Scene
from fastapi.testclient import TestClient
from app.main import app
from app.services import jianying, library, preview, projects


def test_web_ui_and_health():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    page = client.get("/")
    assert page.status_code == 200
    assert "B-roll Workflow" in page.text


def test_split_script():
    project = projects.create_project("測試")
    project.script = "第一句。第二句！\n第三句？"
    project = projects.split_script(project)
    assert [x.narration for x in project.scenes] == ["第一句。", "第二句！", "第三句？"]


def test_global_material_library_search_and_reuse():
    if settings.library_path.exists():
        settings.library_path.unlink()
    project = Project(
        id="library-test", name="library",
        scenes=[
            Scene(id="S001", order=1, narration="第一幕"),
            Scene(id="S002", order=2, narration="第二幕"),
        ],
    )
    projects.save_project(project)
    asset_path = settings.assets_path / "ocean.mp4"
    asset_path.write_bytes(b"test")
    asset = MaterialAsset(
        id="demo-ocean", media_type="video",
        local_path=str(asset_path.resolve()), source="demo",
        title="Ocean waves", tags=["ocean", "waves", "coast"],
        search_queries=["rough ocean"],
    )
    library.upsert_asset(asset)
    assert library.list_library("waves")[0].id == "demo-ocean"
    assert library.search_results("rough ocean")[0].source == "local"
    library.assign_asset(project, project.scenes[1], asset)
    loaded = projects.load_project(project.id)
    items = library.list_library()
    assert loaded.scenes[1].selected_asset == str(asset_path.resolve())
    assert "library / S002" in items[0].used_by


def test_preview_with_burned_subtitles():
    project = Project(
        id="preview-test", name="preview",
        scenes=[Scene(id="S001", order=1, narration="測試字幕", start=0, end=1.017)],
    )
    projects.save_project(project)
    base = projects.project_path(project.id)
    audio = base / "audio" / "narration.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    srt = base / "subtitles" / "narration.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n測試字幕\n",
        encoding="utf-8",
    )
    from app.services.ffmpeg_utils import run_ffmpeg
    run_ffmpeg([
        "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-q:a", "5", str(audio),
    ])
    out = preview.build_preview(project, burn_subtitles=True)
    assert out.exists() and out.stat().st_size > 0


def test_jianying_draft_creation():
    project = Project(
        id="jianying-test", name="draft-test",
        scenes=[Scene(id="S001", order=1, narration="測試字幕", start=0, end=1.0)],
    )
    projects.save_project(project)
    base = projects.project_path(project.id)
    audio = base / "audio" / "narration.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    from app.services.ffmpeg_utils import run_ffmpeg
    run_ffmpeg([
        "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1.2",
        "-q:a", "5", str(audio),
    ])
    draft_root = Path(tempfile.mkdtemp(prefix="jianying-drafts-"))
    existing = draft_root / "ci-draft"
    existing.mkdir()
    (existing / ".locked").write_text("busy", encoding="utf-8")

    name = jianying.export_jianying(project, str(draft_root), "ci-draft")
    assert name == "ci-draft_Broll"
    draft_path = draft_root / name
    assert draft_path.exists()
    content = (draft_path / "draft_content.json").read_text(encoding="utf-8")
    data = json.loads(content)
    tracks = {track.get("name"): track for track in data["tracks"]}
    assert len(tracks["main_video"]["segments"]) == 1
    assert len(tracks["narration"]["segments"]) == 1
    assert len(tracks["caption"]["segments"]) == 1
    assert "測試字幕" in content
    assert data["duration"] >= 1_017_000
