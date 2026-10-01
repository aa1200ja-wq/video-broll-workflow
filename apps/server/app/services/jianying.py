from pathlib import Path
from app.config import settings
from app.models import Project
from app.services.preview import build_scene_clips
from app.services.projects import project_path


def export_jianying(project: Project, draft_folder: str, draft_name: str | None = None) -> str:
    try:
        import pyJianYingDraft as draft
    except ImportError as exc:
        raise RuntimeError("剪映草稿元件未安裝，請重新啟動工具") from exc

    if not project.scenes or any(scene.end <= scene.start for scene in project.scenes):
        raise ValueError("請先完成旁白與時間碼")
    target_folder = draft_folder.strip() or settings.jianying_draft_dir.strip()
    if not target_folder:
        raise ValueError("請先在設定中指定剪映草稿資料夾")
    root = Path(target_folder)
    if not root.exists():
        raise ValueError("剪映草稿資料夾不存在")

    base = project_path(project.id)
    clips = build_scene_clips(project)
    name = (draft_name or project.name).strip() or "B-roll Workflow"
    folder = draft.DraftFolder(str(root))
    script = folder.create_draft(name, project.width, project.height, allow_replace=True)
    script.append_tracks([
        draft.TrackSpec(draft.TrackType.audio, "narration"),
        draft.TrackSpec(draft.TrackType.video, "main_video"),
        draft.TrackSpec(draft.TrackType.text, "caption"),
    ])
    for scene, clip in zip(project.scenes, clips):
        timerange = draft.trange_seconds(scene.start, duration=scene.duration)
        script.add_segment(draft.VideoSegment(str(clip), timerange), "main_video")
        script.add_segment(draft.TextSegment(scene.narration, timerange), "caption")

    narration = base / "audio" / "narration.mp3"
    total = project.scenes[-1].end
    if narration.exists():
        from mutagen.mp3 import MP3
        audio_duration = min(total, float(MP3(narration).info.length))
        script.add_segment(
            draft.AudioSegment(
                str(narration),
                draft.trange_seconds(0, duration=max(0.1, audio_duration)),
            ),
            "narration",
        )
    script.save()
    return name
