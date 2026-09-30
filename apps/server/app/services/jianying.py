from pathlib import Path
from app.models import Project
from app.services.preview import build_scene_clips
from app.services.projects import project_path


def export_jianying(project: Project, draft_folder: str, draft_name: str | None = None) -> str:
    try:
        import pyJianYingDraft as draft
    except ImportError as exc:
        raise RuntimeError("尚未安裝 pyJianYingDraft，請先執行 setup.bat") from exc

    root = Path(draft_folder)
    if not root.exists():
        raise ValueError("剪映草稿資料夾不存在")
    base = project_path(project.id)
    clips = build_scene_clips(project)
    name = draft_name or project.name
    folder = draft.DraftFolder(str(root))
    script = folder.create_draft(name, project.width, project.height, allow_replace=True)
    script.append_tracks([
        draft.TrackSpec(draft.TrackType.audio, "narration"),
        draft.TrackSpec(draft.TrackType.video, "main_video"),
        draft.TrackSpec(draft.TrackType.text, "caption"),
    ])
    for scene, clip in zip(project.scenes, clips):
        timerange = draft.trange_seconds(scene.start, duration=scene.duration)
        segment = draft.VideoSegment(str(clip), timerange)
        script.add_segment(segment, "main_video")
        text = draft.TextSegment(scene.narration, timerange)
        script.add_segment(text, "caption")
    narration = base / "audio" / "narration.mp3"
    total = project.scenes[-1].end if project.scenes else 0
    if narration.exists() and total > 0:
        audio = draft.AudioSegment(str(narration), draft.trange_seconds(0, duration=total))
        script.add_segment(audio, "narration")
    script.save()
    return name
