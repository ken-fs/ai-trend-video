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
  python3 trendclip.py frames my_clip.mp4          # one still per shot
  python3 trendclip.py compare original.mp4 mine.mp4 --labels "Original,Me"   # "trend vs me" video
  python3 trendclip.py match original.mp4 repost.mp4                          # same sound? at what offset?

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


def has_filter(name: str) -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], text=True, capture_output=True).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if len(line.split()) > 1)


def label_filter(text: str) -> str:
    safe = text.replace("\\", "").replace("'", "").replace(":", " ")
    return (f"drawtext=text='{safe}':x=24:y=24:fontsize=h/22:fontcolor=white:"
            "box=1:boxcolor=black@0.55:boxborderw=12")


def cmd_compare(args: argparse.Namespace) -> None:
    """Original and your version next to each other: the "trend vs me" post."""
    need("ffmpeg"), need("ffprobe")
    a, b = probe(args.original), probe(args.mine)
    duration = min(a["duration"], b["duration"])
    portrait = a["height"] > a["width"]
    if args.layout == "side":  # same height, next to each other (two portrait clips → 1080x960-ish, two landscape → 1920x540)
        size, stack = f"scale=-2:{960 if portrait else 540},setsar=1", "hstack=inputs=2"
    else:  # same width, one above the other
        size, stack = f"scale={540 if portrait else 960}:-2,setsar=1", "vstack=inputs=2"
    labels = [x.strip() for x in args.labels.split(",")] if args.labels else []
    use_labels = len(labels) == 2 and has_filter("drawtext")
    if labels and not use_labels:
        print("note: this ffmpeg has no drawtext filter, so the labels are left out")
    la = f",{label_filter(labels[0])}" if use_labels else ""
    lb = f",{label_filter(labels[1])}" if use_labels else ""
    src = 0 if args.audio == "original" else 1
    has_audio = (a if src == 0 else b)["has_audio"]

    def render(la: str, lb: str) -> None:
        graph = f"[0:v]{size}{la}[a];[1:v]{size}{lb}[b];[a][b]{stack}[v]"
        run(["ffmpeg", "-v", "error", "-y", "-i", args.original, "-i", args.mine, "-filter_complex", graph,
             "-map", "[v]"] + (["-map", f"{src}:a"] if has_audio else []) + [
             "-t", f"{duration}", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", args.out])

    try:
        render(la, lb)
    except subprocess.CalledProcessError:
        if not use_labels:
            raise
        print("note: drawing the labels failed (often a missing font), so they are left out")
        render("", "")
    print(f"wrote {args.out} ({args.layout}, {duration} s, sound from {args.audio})")


def cmd_frames(args: argparse.Namespace) -> None:
    """One still per shot, taken just after each cut (for image-to-video tools, thumbnails or a storyboard)."""
    need("ffmpeg"), need("ffprobe")
    info = probe(args.source)
    os.makedirs(args.out, exist_ok=True)
    shots = shot_list(find_cuts(args.source, args.threshold), info["duration"])
    for s in shots:
        t = s["start"] + min(0.2, s["length"] / 3)  # a moment after the cut, so it isn't a blend of two shots
        dst = os.path.join(args.out, f"shot-{s['shot']:02d}.jpg")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", args.source, "-frames:v", "1", "-q:v", "2", dst])
        print(f"{dst}  shot {s['shot']} at {t:.2f} s ({s['start']}–{s['end']} s)")


ENV_RATE = 50  # loudness samples per second for match (one every 20 ms)
BANDS = ["lowpass=f=250", "bandpass=f=1200:width_type=o:w=2", "highpass=f=3500"]  # bass, mids (voice), highs (hats, claps)


def onset_envelopes(path: str, max_seconds: float) -> list[list[float]]:
    """For each band: how much louder each 20 ms gets than the one before. Robust to volume and voice-over level."""
    import array
    out = []
    step = 8000 // ENV_RATE
    for band in BANDS:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-t", f"{max_seconds}", "-vn", "-ac", "1", "-af", band,
                              "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
        pcm = array.array("h")
        pcm.frombytes(raw[: len(raw) // 2 * 2])
        energy = [math.log1p(sum(abs(v) for v in pcm[i:i + step]) / step) for i in range(0, len(pcm) - step + 1, step)]
        out.append([max(0.0, e - p) for p, e in zip([energy[0]] + energy, energy)] if energy else [])
    return out


def pearson(xa: list[float], xb: list[float]) -> float | None:
    n = len(xa)
    ma, mb = sum(xa) / n, sum(xb) / n
    va = sum((x - ma) ** 2 for x in xa)
    vb = sum((y - mb) ** 2 for y in xb)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(xa, xb)) / math.sqrt(va * vb)


def correlate(a: list[list[float]], b: list[list[float]], min_overlap: int) -> tuple[float, int]:
    """Slide b against a; score = mean correlation over the bands. Returns (score, offset): b[0] lines up with a[offset]."""
    la, lb = len(a[0]), len(b[0])
    best = (-1.0, 0)
    for off in range(-(lb - min_overlap), la - min_overlap + 1):
        sa, sb = max(0, off), max(0, -off)
        n = min(la - sa, lb - sb)
        if n < min_overlap:
            continue
        rs = [pearson(ba[sa:sa + n], bb[sb:sb + n]) for ba, bb in zip(a, b)]
        rs = [r for r in rs if r is not None]
        if rs and sum(rs) / len(rs) > best[0]:
            best = (sum(rs) / len(rs), off)
    return best


def cmd_match(args: argparse.Namespace) -> None:
    """Do two videos use the same sound, and where does one start inside the other?"""
    need("ffmpeg")
    a = onset_envelopes(args.a, args.max_seconds)
    b = onset_envelopes(args.b, args.max_seconds)
    if not a[0] or not b[0]:
        sys.exit("trendclip: one of the files has no sound")
    score, off = correlate(a, b, min(len(a[0]), len(b[0]), ENV_RATE * 3))
    sec = off / ENV_RATE
    # 14 Nov 2026 tests: the same sound scored 0.82–1.00 (excerpts, re-encodes, a Reel repost); different dance tracks up to 0.41
    verdict = "same sound" if score >= 0.65 else "maybe the same sound (check by ear)" if score >= 0.5 else "different sound"
    na, nb = (args.a, args.b) if os.path.basename(args.a) == os.path.basename(args.b) else (os.path.basename(args.a), os.path.basename(args.b))
    where = f"{nb} starts {sec:.2f} s into {na}" if sec >= 0 else f"{na} starts {-sec:.2f} s into {nb}"
    print(f"{verdict}: score {score:.2f}" + (f"; {where}" if score >= 0.5 else ""))


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
    comp = sub.add_parser("compare", help='put the original and your version next to each other ("trend vs me")')
    comp.add_argument("original")
    comp.add_argument("mine")
    comp.add_argument("--layout", choices=["side", "stack"], default="side", help="side by side (default) or one above the other")
    comp.add_argument("--labels", help='two labels, e.g. "Original,Me" (needs an ffmpeg with drawtext)')
    comp.add_argument("--audio", choices=["original", "mine"], default="original", help="whose sound to keep (default: original)")
    comp.add_argument("--out", default="compare.mp4")
    comp.set_defaults(func=cmd_compare)
    fr = sub.add_parser("frames", help="save one still per shot")
    fr.add_argument("source")
    fr.add_argument("--out", default="frames")
    fr.add_argument("--threshold", type=float, default=0.25)
    fr.set_defaults(func=cmd_frames)
    ma = sub.add_parser("match", help="check whether two videos use the same sound, and the offset between them")
    ma.add_argument("a", help="usually the longer one (the full song, or the original post)")
    ma.add_argument("b", help="the clip to look for in it (a repost, a remake, your edit)")
    ma.add_argument("--max-seconds", type=float, default=120, help="only read this much of each file (default 120)")
    ma.set_defaults(func=cmd_match)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
