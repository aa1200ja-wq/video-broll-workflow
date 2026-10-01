import asyncio
from pathlib import Path
from app.models import Project
from app.services.ffmpeg_utils import run_ffmpeg
from app.services.projects import project_path, save_project


def _duration(path: Path) -> float:
    try:
        from mutagen.mp3 import MP3
        return max(0.1, float(MP3(path).info.length))
    except Exception as exc:
        raise RuntimeError(f"無法讀取旁白長度：{path.name}") from exc


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


async def synthesize(project: Project, voice: str, rate: str, pitch: str) -> Project:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("尚未安裝 edge-tts，請重新執行 START_HERE.cmd") from exc

    base = project_path(project.id)
    scene_dir = base / "audio" / "scenes"
    scene_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    cursor = 0.0
    for scene in project.scenes:
        target = scene_dir / f"{scene.id}.mp3"
        comm = edge_tts.Communicate(
            scene.narration, voice=voice, rate=rate, pitch=pitch
        )
        await comm.save(str(target))
        duration = _duration(target)
        scene.start = cursor
        scene.end = cursor + duration
        scene.status = "ready_for_asset"
        cursor = scene.end
        clips.append(target)

    concat_file = base / "audio" / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{clip.as_posix()}'" for clip in clips), encoding="utf-8"
    )
    narration = base / "audio" / "narration.mp3"
    run_ffmpeg([
        "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:a", "libmp3lame", "-q:a", "2", str(narration),
    ])
    lines: list[str] = []
    for i, scene in enumerate(project.scenes, start=1):
        lines.extend([
            str(i), f"{_srt_time(scene.start)} --> {_srt_time(scene.end)}",
            scene.narration, "",
        ])
    (base / "subtitles" / "narration.srt").write_text("\n".join(lines), encoding="utf-8")
    project.voice, project.rate, project.pitch = voice, rate, pitch
    return save_project(project)


def synthesize_sync(project: Project, voice: str, rate: str, pitch: str) -> Project:
    return asyncio.run(synthesize(project, voice, rate, pitch))
