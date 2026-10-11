#!/usr/bin/env python3
import argparse
import shlex
import subprocess
from pathlib import Path
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将人物演奏视频和外录音频裁剪并合成为音画同步的架子鼓演奏视频。"
    )
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--video-in", required=True, type=float)
    parser.add_argument("--audio-in", required=True, type=float)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audio-tempo", type=float, default=1.0)
    parser.add_argument("--brighten", action="store_true")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()
def require_valid(args: argparse.Namespace) -> None:
    if not args.video.is_file():
        raise SystemExit(f"找不到视频文件：{args.video}")
    if not args.audio.is_file():
        raise SystemExit(f"找不到音频文件：{args.audio}")
    if args.video_in < 0 or args.audio_in < 0 or args.duration <= 0:
        raise SystemExit("视频和音频入点不能为负数，成片时长必须大于零。")
    if not 0.95 <= args.audio_tempo <= 1.05:
        raise SystemExit("拒绝使用 0.95–1.05 以外的音频速度；请重新检查漂移锚点。")
def build_command(args: argparse.Namespace) -> list[str]:
    video_filter = "setpts=PTS-STARTPTS"
    if args.brighten:
        video_filter += ",eq=brightness=0.055:contrast=1.025:saturation=1.09:gamma=1.045"
    audio_filter = "asetpts=PTS-STARTPTS"
    if args.audio_tempo != 1.0:
        audio_filter += f",atempo={args.audio_tempo:.9f}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    return [
        "ffmpeg", "-hide_banner", "-y",
        "-ss", f"{args.video_in:.6f}", "-i", str(args.video),
        "-ss", f"{args.audio_in:.6f}", "-i", str(args.audio),
        "-t", f"{args.duration:.6f}",
        "-filter_complex", f"[0:v]{video_filter}[v];[1:a]{audio_filter}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k",
        "-movflags", "+faststart", "-shortest", str(args.output),
    ]
def main() -> None:
    args = parse_args()
    require_valid(args)
    command = build_command(args)
    print(shlex.join(command))
    if not args.dry_run:
        subprocess.run(command, check=True)
if __name__ == "__main__":
    main()
