from pathlib import Path
from app.models import Project, Scene
from app.services.ffmpeg_utils import run_ffmpeg
from app.services.projects import project_path


def _clip_for_scene(project: Project, scene: Scene) -> Path:
    base = project_path(project.id)
    out_dir = base / "exports" / "scene_clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{scene.id}.mp4"
    duration = max(0.1, scene.duration or 4.0)
    scale = f"scale={project.width}:{project.height}:force_original_aspect_ratio=increase,crop={project.width}:{project.height},fps=30"
    if scene.selected_asset:
        source = Path(scene.selected_asset)
        if scene.selected_asset_type == "image":
            args = [
                "-y", "-loop", "1", "-t", f"{duration:.3f}",
                "-i", str(source), "-vf", scale, "-an", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", str(target),
            ]
        else:
            args = [
                "-y", "-stream_loop", "-1", "-i", str(source),
                "-t", f"{duration:.3f}", "-vf", scale, "-an", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", str(target),
            ]
    else:
        args = [
            "-y", "-f", "lavfi", "-i",
            f"color=c=0x202020:s={project.width}x{project.height}:r=30",
            "-t", f"{duration:.3f}", "-an", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", str(target),
        ]
    run_ffmpeg(args)
    return target


def build_scene_clips(project: Project) -> list[Path]:
    return [_clip_for_scene(project, scene) for scene in project.scenes]


def build_preview(project: Project, burn_subtitles: bool = False) -> Path:
    base = project_path(project.id)
    clips = build_scene_clips(project)
    concat = base / "exports" / "clips.txt"
    concat.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips), encoding="utf-8")
    silent = base / "exports" / "silent.mp4"
    run_ffmpeg([
        "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", str(silent),
    ])
    narration = base / "audio" / "narration.mp3"
    if not narration.exists():
        raise RuntimeError("請先產生旁白")
    merged = base / "exports" / "preview_base.mp4"
    run_ffmpeg([
        "-y", "-i", str(silent), "-i", str(narration),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(merged),
    ])
    if not burn_subtitles:
        final = base / "exports" / "preview.mp4"
        final.write_bytes(merged.read_bytes())
        return final
    srt = base / "subtitles" / "narration.srt"
    final = base / "exports" / "preview.mp4"
    escaped = str(srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    run_ffmpeg([
        "-y", "-i", str(merged), "-vf", f"subtitles='{escaped}'",
        "-c:v", "libx264", "-c:a", "copy", str(final),
    ])
    return final
