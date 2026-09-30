import os
import tempfile
from pathlib import Path

os.environ["PROJECTS_DIR"] = tempfile.mkdtemp(prefix="broll-tests-")

from app.models import Project, Scene
from app.services import preview, projects


def test_split_script():
    project = projects.create_project("測試")
    project.script = "第一句。第二句！\n第三句？"
    project = projects.split_script(project)
    assert [x.narration for x in project.scenes] == ["第一句。", "第二句！", "第三句？"]


def test_preview_placeholder():
    project = Project(
        id="preview-test", name="preview",
        scenes=[Scene(id="S001", order=1, narration="測試", start=0, end=1.0)],
    )
    projects.save_project(project)
    base = projects.project_path(project.id)
    audio = base / "audio" / "narration.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    import subprocess
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-q:a", "5", str(audio),
    ], check=True, capture_output=True)
    out = preview.build_preview(project)
    assert out.exists() and out.stat().st_size > 0
