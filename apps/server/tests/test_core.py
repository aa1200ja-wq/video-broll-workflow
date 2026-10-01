import json
import os
import tempfile
from pathlib import Path

_temp_root = tempfile.mkdtemp(prefix="broll-tests-")
os.environ["BROLL_DATA_DIR"] = _temp_root
os.environ["PROJECTS_DIR"] = str(Path(_temp_root) / "projects")

from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.models import MaterialAsset, Project, Scene
from app.services import jianying, library, preview, projects
from app.services.ffmpeg_utils import run_ffmpeg


def test_web_ui_health_and_format():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert "B-roll Workflow" in client.get("/").text
    project = client.post("/api/projects", json={"name": "format-test"}).json()
    updated = client.put(
        f"/api/projects/{project['id']}/format", json={"ratio": "9:16"}
    ).json()
    assert (updated["width"], updated["height"]) == (1080, 1920)


def test_split_script():
    project = projects.create_project("測試")
    project.script = "第一句。第二句！\n第三句？"
    project = projects.split_script(project)
    assert [x.narration for x in project.scenes] == ["第一句。", "第二句！", "第三句？"]


def test_global_library_merges_all_projects_and_filters_orientation():
    if settings.library_path.exists():
        settings.library_path.unlink()
    p1 = projects.create_project("A")
    p2 = projects.create_project("B")
    a_path = settings.assets_path / "a.mp4"
    b_path = settings.assets_path / "b.mp4"
    a_path.write_bytes(b"x")
    b_path.write_bytes(b"y")
    a = MaterialAsset(
        id="land", media_type="video", local_path=str(a_path),
        source="demo", title="ocean landscape", search_queries=["ocean"],
        width=1920, height=1080,
    )
    b = MaterialAsset(
        id="port", media_type="video", local_path=str(b_path),
        source="demo", title="ocean portrait", search_queries=["ocean"],
        width=1080, height=1920,
    )
    (projects.project_path(p1.id) / "library.json").write_text(
        json.dumps([a.model_dump()], ensure_ascii=False), encoding="utf-8"
    )
    library.save_library([a])
    (projects.project_path(p2.id) / "library.json").write_text(
        json.dumps([b.model_dump()], ensure_ascii=False), encoding="utf-8"
    )
    items = library.list_library()
    assert {x.id for x in items} >= {"land", "port"}
    assert [x.id for x in library.search_results("ocean", "landscape")] == ["land"]
    assert [x.id for x in library.search_results("ocean", "portrait")] == ["port"]


def test_preview_defaults_to_burned_subtitles():
    project = Project(
        id="preview-test", name="preview",
        scenes=[Scene(id="S001", order=1, narration="測試字幕 TEST", start=0, end=1.0)],
    )
    projects.save_project(project)
    base = projects.project_path(project.id)
    audio = base / "audio" / "narration.mp3"
    run_ffmpeg([
        "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-q:a", "5", str(audio),
    ])
    (base / "subtitles" / "narration.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n測試字幕 TEST\n",
        encoding="utf-8",
    )
    out = preview.build_preview(project)
    assert out.exists() and out.stat().st_size > 0
    assert (base / "exports" / "preview_base.mp4").exists()


def test_jianying_handles_media_shorter_than_scene():
    project = Project(
        id="jianying-test", name="draft-test",
        scenes=[Scene(id="S001", order=1, narration="測試字幕", start=0, end=1.017)],
    )
    projects.save_project(project)
    base = projects.project_path(project.id)
    audio = base / "audio" / "narration.mp3"
    run_ffmpeg([
        "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1.0",
        "-q:a", "5", str(audio),
    ])
    draft_root = Path(tempfile.mkdtemp(prefix="jianying-drafts-"))
    existing = draft_root / "ci-draft"
    existing.mkdir()
    (existing / ".locked").write_text("busy", encoding="utf-8")

    name = jianying.export_jianying(project, str(draft_root), "ci-draft")
    assert name == "ci-draft_Broll"
    content = (draft_root / name / "draft_content.json").read_text(encoding="utf-8")
    data = json.loads(content)
    tracks = {track.get("name"): track for track in data["tracks"]}
    assert len(tracks["main_video"]["segments"]) == 1
    assert len(tracks["narration"]["segments"]) == 1
    assert len(tracks["caption"]["segments"]) == 1
    assert "測試字幕" in content
    assert data["duration"] >= 1_017_000
