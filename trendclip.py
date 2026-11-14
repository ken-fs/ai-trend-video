#!/usr/bin/env python3
"""trendclip: get a viral TikTok / Reels clip ready to remake.

Give it a link (or a video file) and it will:
  1. download the original clip (yt-dlp: TikTok, YouTube Shorts, Instagram Reels, Facebook, X and more)
  2. find every camera cut (ffmpeg scene detection)
  3. crop it to 9:16 or 16:9 without cutting people off, and scale it to 720p
  4. export the original sound as MP3
  5. make an optional short version (for example the first 7 seconds)
  6. save a contact sheet (one frame every half second) and a shot list

Needs ffmpeg / ffprobe on PATH, and yt-dlp if you pass a URL. Python standard library only.

  python3 trendclip.py prep "https://www.tiktok.com/@user/video/123" --ratio 16:9 --short 7
  python3 trendclip.py prep my_clip.mp4 --ratio 9:16 --out wassup
  python3 trendclip.py cuts my_clip.mp4            # only print the cut times

Made by the TrendTemplate team (https://trendtemplate.com). MIT license.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys

RATIOS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1), "4:5": (4, 5), "3:4": (3, 4)}


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def need(tool: str) -> None:
    if not shutil.which(tool):
        sys.exit(f"trendclip: '{tool}' not found. Install it first (macOS: brew install {tool}).")


def probe(path: str) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path]).stdout
    data = json.loads(out)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if not video:
        sys.exit(f"trendclip: no video stream in {path}")
    num, den = (video.get("r_frame_rate") or "30/1").split("/")
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(int(num) / max(int(den), 1), 2),
        "duration": round(float(data["format"]["duration"]), 2),
        "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def download(url: str, out_dir: str, cookies_from: str | None, cookies_file: str | None = None) -> str:
    need("yt-dlp")
    target = os.path.join(out_dir, "original.%(ext)s")
    # best picture first, preferring H.264 + AAC so every editor opens it; merged into one MP4
    cmd = ["yt-dlp", "-q", "--no-playlist", "-f", "bv*+ba/b", "-S", "res,vcodec:h264,acodec:m4a",
           "--merge-output-format", "mp4", "-o", target, url]
    if cookies_from:
        cmd[1:1] = ["--cookies-from-browser", cookies_from]
    if cookies_file:
        cmd[1:1] = ["--cookies", cookies_file]
    try:
        run(cmd)
    except subprocess.CalledProcessError as e:
        hint = "" if cookies_from or cookies_file else ("\nSome posts need a logged-in browser (YouTube often asks for it, private or age-gated posts too): "
                                        "add --cookies-from-browser chrome (or firefox / safari / edge)")
        sys.exit(f"trendclip: download failed.\n{e.stderr.strip()}{hint}")
    for name in os.listdir(out_dir):
        if name.startswith("original."):
            return os.path.join(out_dir, name)
    sys.exit("trendclip: yt-dlp finished but no file was written")


def find_cuts(path: str, threshold: float) -> list[float]:
    """Times (seconds) where the picture changes enough to count as a camera cut."""
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{threshold})',showinfo",
                           "-an", "-f", "null", "-"], text=True, capture_output=True)
    times = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]
    cuts: list[float] = []
    for t in times:  # drop flashes that fire twice within half a second
        if not cuts or t - cuts[-1] > 0.5:
            cuts.append(round(t, 2))
    return cuts


def crop_box(w: int, h: int, ratio: tuple[int, int]) -> tuple[int, int, int, int]:
    """Largest centred crop with the target ratio. Returns (cw, ch, x, y), all even numbers."""
    rw, rh = ratio
    if w * rh > h * rw:  # source is wider than target: cut the sides
        ch, cw = h, int(h * rw / rh)
    else:  # source is taller than target: cut top and bottom
        cw, ch = w, int(w * rh / rw)
    cw, ch = cw - cw % 2, ch - ch % 2
    return cw, ch, (w - cw) // 2 // 2 * 2, (h - ch) // 2 // 2 * 2


def target_size(ratio: tuple[int, int]) -> tuple[int, int]:
    rw, rh = ratio
    if rw >= rh:  # landscape / square: 720 tall
        return int(720 * rw / rh) // 2 * 2, 720
    return 720, int(720 * rh / rw) // 2 * 2


def export(src: str, dst_mp4: str, dst_mp3: str | None, seconds: float | None, vf: str) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
    if seconds:
        cmd += ["-t", f"{seconds}"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst_mp4]
    run(cmd)
    if dst_mp3:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src] + (["-t", f"{seconds}"] if seconds else [])
        run(cmd + ["-vn", "-c:a", "libmp3lame", "-b:a", "192k", dst_mp3])


def contact_sheet(src: str, dst: str, duration: float, every: float = 0.5, cols: int = 6) -> None:
    frames = max(1, math.ceil(duration / every))
    rows = math.ceil(frames / cols)
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
         f"fps={1 / every},scale=320:-2,tile={cols}x{rows}", "-frames:v", "1", "-q:v", "3", dst])


def shot_list(cuts: list[float], duration: float) -> list[dict]:
    edges = [0.0] + [c for c in cuts if 0 < c < duration] + [duration]
    return [{"shot": i + 1, "start": round(a, 2), "end": round(b, 2), "length": round(b - a, 2)}
            for i, (a, b) in enumerate(zip(edges, edges[1:]))]


def write_report(out_dir: str, source: str, info: dict, ratio: str, cuts: list[float], short: float | None) -> None:
    shots = shot_list(cuts, info["duration"])
    report = {"source": source if re.match(r"https?://", source) else os.path.basename(source), "original": info, "ratio": ratio, "cuts": cuts, "shots": shots, "short_seconds": short}
    with open(os.path.join(out_dir, "shots.json"), "w") as f:
        json.dump(report, f, indent=2)
    label = source if re.match(r"https?://", source) else os.path.basename(source)
    lines = [f"# Shot list: {label}", "",
             f"Original: {info['width']}x{info['height']}, {info['fps']} fps, {info['duration']} s, "
             f"{'with' if info['has_audio'] else 'no'} sound. Exported as {ratio} at 720p.", "",
             "| Shot | Start | End | Length |", "|---|---|---|---|"]
    lines += [f"| {s['shot']} | {s['start']} s | {s['end']} s | {s['length']} s |" for s in shots]
    if short:
        on_cut = next((c for c in cuts if abs(c - short) <= 0.1), None)
        inside = [c for c in cuts if c < short - 0.1]
        last = inside[-1] if inside else 0
        if on_cut is not None:
            lines += ["", f"Short version: first {short:g} s. It ends right on the cut after shot {len(inside) + 1}."]
        else:
            lines += ["", f"Short version: first {short:g} s. It ends {round(short - last, 2)} s into shot {len(inside) + 1}."
                      + (" That's less than a second, so it may stop mid-move: pick a length that ends on a cut."
                         if short - last < 1 else "")]
    lines += ["", "Files: `clip.mp4` / `clip.mp3` (full length)"
              + (f", `clip-{short:g}s.mp4` / `clip-{short:g}s.mp3`" if short else "") + ", `sheet.jpg` (one frame every 0.5 s).",
              "", "Want to put a face in it without filming? Many of these trends are on https://trendtemplate.com "
              "(upload a photo, get the original clip with your face and the original sound)."]
    with open(os.path.join(out_dir, "SHOTS.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def cmd_prep(args: argparse.Namespace) -> None:
    need("ffmpeg"), need("ffprobe")
    os.makedirs(args.out, exist_ok=True)
    src = args.source if os.path.exists(args.source) else download(args.source, args.out, args.cookies_from_browser, args.cookies)
    info = probe(src)
    ratio = RATIOS.get(args.ratio)
    if not ratio:
        sys.exit(f"trendclip: --ratio must be one of {', '.join(RATIOS)}")
    cw, ch, x, y = crop_box(info["width"], info["height"], ratio)
    if args.y_offset is not None:
        y = max(0, min(info["height"] - ch, args.y_offset)) // 2 * 2
    if args.x_offset is not None:
        x = max(0, min(info["width"] - cw, args.x_offset)) // 2 * 2
    tw, th = target_size(ratio)
    vf = f"crop={cw}:{ch}:{x}:{y},scale={tw}:{th},setsar=1"
    cuts = find_cuts(src, args.threshold)
    export(src, os.path.join(args.out, "clip.mp4"), os.path.join(args.out, "clip.mp3") if info["has_audio"] else None, None, vf)
    if args.short:
        export(src, os.path.join(args.out, f"clip-{args.short:g}s.mp4"),
               os.path.join(args.out, f"clip-{args.short:g}s.mp3") if info["has_audio"] else None, args.short, vf)
    contact_sheet(os.path.join(args.out, "clip.mp4"), os.path.join(args.out, "sheet.jpg"), info["duration"])
    write_report(args.out, args.source, info, args.ratio, cuts, args.short)
    print(f"{info['width']}x{info['height']} {info['duration']} s · {len(cuts) + 1} shots · cuts at "
          f"{', '.join(f'{c} s' for c in cuts) or 'none'}")
    print(f"crop {cw}x{ch} at ({x},{y}) → {tw}x{th}. Look at {args.out}/sheet.jpg to check nobody is cut off "
          f"(move the crop with --x-offset / --y-offset).")
    print(f"wrote {args.out}/SHOTS.md and shots.json")


def cmd_cuts(args: argparse.Namespace) -> None:
    need("ffmpeg"), need("ffprobe")
    info = probe(args.source)
    cuts = find_cuts(args.source, args.threshold)
    for s in shot_list(cuts, info["duration"]):
        print(f"shot {s['shot']}: {s['start']:>6} – {s['end']:>6} s  ({s['length']} s)")


def main() -> None:
    p = argparse.ArgumentParser(prog="trendclip", description="Get a viral clip ready to remake: download, find cuts, crop, export sound.")
    sub = p.add_subparsers(dest="cmd", required=True)
    prep = sub.add_parser("prep", help="download (or read) a clip and export everything")
    prep.add_argument("source", help="TikTok, YouTube Shorts, Instagram Reels, Facebook, X… URL, or a local video file")
    prep.add_argument("--ratio", default="9:16", help="output ratio: 9:16 (default), 16:9, 1:1, 4:5, 3:4")
    prep.add_argument("--short", type=float, help="also export the first N seconds (for example 7)")
    prep.add_argument("--out", default="trendclip-out", help="output folder (default: trendclip-out)")
    prep.add_argument("--threshold", type=float, default=0.25, help="scene-cut sensitivity, 0–1 (default 0.25; lower finds more cuts)")
    prep.add_argument("--y-offset", type=int, help="top edge of the crop in pixels (when heads or feet get cut)")
    prep.add_argument("--x-offset", type=int, help="left edge of the crop in pixels (when someone at the side gets cut)")
    prep.add_argument("--cookies-from-browser", help="for posts that need a login, e.g. chrome")
    prep.add_argument("--cookies", help="a cookies.txt file (Netscape format), when YouTube keeps asking you to sign in")
    prep.set_defaults(func=cmd_prep)
    cuts = sub.add_parser("cuts", help="print the shot list of a local file")
    cuts.add_argument("source")
    cuts.add_argument("--threshold", type=float, default=0.25)
    cuts.set_defaults(func=cmd_cuts)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
