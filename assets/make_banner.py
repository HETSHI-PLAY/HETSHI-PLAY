#!/usr/bin/env python3
"""
Generate assets/banner.gif — animated SOC / terminal banner for the
HETSHI-PLAY GitHub profile.

Requires: pycairo, ImageMagick (convert). Run from the repo root:
    python3 assets/make_banner.py
"""

import math
import os
import shutil
import subprocess
import tempfile

import cairo

W, H = 1000, 360
FRAMES = 60
DELAY_CS = 8  # 1/100 s per frame -> 80 ms

CYAN = (0.133, 0.827, 0.933)
BLUE = (0.231, 0.510, 0.965)
GREEN = (0.204, 0.827, 0.600)
TEXT = (0.886, 0.910, 0.941)
MUTED = (0.392, 0.455, 0.545)
DARK = (0.024, 0.043, 0.082)

FONT = "DejaVu Sans Mono"


def rgba(color, alpha=1.0):
    return (color[0], color[1], color[2], alpha)


def spaced_text(ctx, x, y, text, spacing):
    for ch in text:
        ctx.show_text(ch)
        ctx.move_to(ctx.get_current_point()[0] + spacing, y)


def typed(text, frame, start, end):
    if frame < start:
        return ""
    if frame >= end:
        return text
    n = int((frame - start) / (end - start) * len(text)) + 1
    return text[:n]


def draw_background(ctx, frame):
    grad = cairo.LinearGradient(0, 0, W, H)
    grad.add_color_stop_rgb(0, 0.024, 0.043, 0.082)
    grad.add_color_stop_rgb(0.55, 0.035, 0.063, 0.110)
    grad.add_color_stop_rgb(1, 0.020, 0.055, 0.090)
    ctx.set_source(grad)
    ctx.paint()

    # subtle grid
    ctx.set_line_width(1)
    for x in range(0, W, 32):
        ctx.set_source_rgba(0.133, 0.827, 0.933, 0.045 if x % 160 else 0.09)
        ctx.move_to(x + 0.5, 0)
        ctx.line_to(x + 0.5, H)
        ctx.stroke()
    for y in range(0, H, 32):
        ctx.set_source_rgba(0.133, 0.827, 0.933, 0.045 if y % 160 else 0.09)
        ctx.move_to(0, y + 0.5)
        ctx.line_to(W, y + 0.5)
        ctx.stroke()

    # vignette-ish corners
    radial = cairo.RadialGradient(W * 0.78, H * 0.42, 10, W * 0.78, H * 0.42, 520)
    radial.add_color_stop_rgba(0, 0.133, 0.827, 0.933, 0.10)
    radial.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(radial)
    ctx.paint()

    # moving scanline
    y = (frame / FRAMES) * (H + 40) - 20
    grad2 = cairo.LinearGradient(0, y - 18, 0, y + 18)
    grad2.add_color_stop_rgba(0, 0.133, 0.827, 0.933, 0)
    grad2.add_color_stop_rgba(0.5, 0.133, 0.827, 0.933, 0.06)
    grad2.add_color_stop_rgba(1, 0.133, 0.827, 0.933, 0)
    ctx.set_source(grad2)
    ctx.rectangle(0, y - 18, W, 36)
    ctx.fill()


def draw_title(ctx, frame):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(56)

    ctx.set_source_rgba(0.133, 0.827, 0.933, 0.16)
    for dx, dy in ((0, 2), (2, 0), (-2, 0)):
        ctx.move_to(58 + dx, 96 + dy)
        ctx.show_text("HETSHI-PLAY")

    grad = cairo.LinearGradient(58, 60, 520, 96)
    grad.add_color_stop_rgb(0, 0.93, 0.96, 1.0)
    grad.add_color_stop_rgb(1, 0.133, 0.827, 0.933)
    ctx.set_source(grad)
    ctx.move_to(58, 96)
    ctx.show_text("HETSHI-PLAY")

    # label
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12)
    ctx.set_source_rgba(*rgba(MUTED, 0.9))
    ctx.move_to(60, 40)
    spaced_text(ctx, 60, 40, "// PROFILE", 2.4)

    # subtitle
    ctx.set_font_size(14)
    ctx.set_source_rgba(*rgba(CYAN, 0.92))
    ctx.move_to(60, 128)
    spaced_text(ctx, 60, 128, "BLUE TEAM   ·   SOC   ·   CTF", 3.2)

    # animated accent bar
    w = min(1.0, frame / 12) * 210
    bar = cairo.LinearGradient(60, 0, 60 + 210, 0)
    bar.add_color_stop_rgb(0, *CYAN)
    bar.add_color_stop_rgb(1, *BLUE)
    ctx.set_source(bar)
    ctx.rectangle(60, 140, max(2, w), 3)
    ctx.fill()


def draw_terminal(ctx, frame):
    x0, y0, x1, y1, r = 56, 172, 742, 342, 10

    # window
    ctx.new_path()
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(x1 - r, y0 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(x1 - r, y1 - r, r, 0, 0.5 * math.pi)
    ctx.arc(x0 + r, y1 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgba(0.031, 0.055, 0.098, 0.72)
    ctx.fill_preserve()
    ctx.set_line_width(1)
    ctx.set_source_rgba(0.133, 0.827, 0.933, 0.28)
    ctx.stroke()

    # header bar
    ctx.rectangle(x0, y0, x1 - x0, 24)
    ctx.set_source_rgba(0.133, 0.827, 0.933, 0.06)
    ctx.fill()
    ctx.set_source_rgba(0.133, 0.827, 0.933, 0.20)
    ctx.move_to(x0, y0 + 24.5)
    ctx.line_to(x1, y0 + 24.5)
    ctx.stroke()

    for i, c in enumerate(((1.0, 0.36, 0.36), (0.98, 0.75, 0.29), (0.30, 0.85, 0.55))):
        ctx.set_source_rgba(c[0], c[1], c[2], 0.85)
        ctx.arc(x0 + 16 + i * 14, y0 + 12, 4, 0, 2 * math.pi)
        ctx.fill()

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(11)
    ctx.set_source_rgba(*rgba(MUTED, 0.95))
    ctx.move_to(x0 + 64, y0 + 16)
    ctx.show_text("hetshi@sec:~  —  zsh")

    # lines
    ctx.set_font_size(14.5)
    lines = [
        (2, 11, "prompt", "$ whoami"),
        (13, 13, "out", "HETSHI-PLAY"),
        (17, 30, "prompt", "$ soc-status --live"),
        (33, 33, "ok", "[ok] wazuh siem ........ connected"),
        (37, 37, "ok", "[ok] threat hunting .... active"),
        (41, 41, "ok", "[ok] ctf mode .......... ready"),
    ]
    y = y0 + 46
    for start, end, kind, text in lines:
        shown = typed(text, frame, start, end)
        if shown:
            ctx.set_source_rgba(*rgba(CYAN if kind == "prompt" else (
                GREEN if kind == "ok" else TEXT), 1.0))
            ctx.move_to(x0 + 18, y)
            ctx.show_text(shown)
        y += 22

    # blinking cursor right after the last line
    if frame >= 45:
        last_y = y0 + 46 + 5 * 22
        ext = ctx.text_extents(lines[-1][3])
        if (frame // 6) % 2 == 0:
            ctx.set_source_rgba(*rgba(CYAN, 1.0))
            ctx.rectangle(x0 + 18 + ext.width + 8, last_y - 13, 9, 17)
            ctx.fill()


def draw_radar(ctx, frame):
    cx, cy, rad = 858, 148, 92
    angle = (frame / FRAMES) * 2 * math.pi - math.pi / 2

    # dish
    ctx.set_source_rgba(0.024, 0.075, 0.110, 0.55)
    ctx.arc(cx, cy, rad, 0, 2 * math.pi)
    ctx.fill()

    # rings
    for i in range(1, 5):
        ctx.set_line_width(1)
        ctx.set_source_rgba(0.133, 0.827, 0.933, 0.16 if i < 4 else 0.30)
        ctx.arc(cx, cy, rad * i / 4, 0, 2 * math.pi)
        ctx.stroke()

    # crosshair
    ctx.set_source_rgba(0.133, 0.827, 0.933, 0.13)
    ctx.move_to(cx - rad, cy)
    ctx.line_to(cx + rad, cy)
    ctx.move_to(cx, cy - rad)
    ctx.line_to(cx, cy + rad)
    ctx.stroke()

    # ticks
    for i in range(60):
        a = i / 60 * 2 * math.pi
        long = i % 5 == 0
        r1 = rad - (9 if long else 5)
        ctx.set_source_rgba(0.133, 0.827, 0.933, 0.30 if long else 0.14)
        ctx.move_to(cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        ctx.line_to(cx + math.cos(a) * rad, cy + math.sin(a) * rad)
        ctx.stroke()

    # sweep trail
    trail = 0.75
    steps = 30
    for k in range(steps):
        a1 = angle - trail * (k / steps)
        a2 = angle - trail * ((k + 1) / steps)
        ctx.new_path()
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, rad - 2, a2, a1)
        ctx.close_path()
        ctx.set_source_rgba(0.133, 0.827, 0.933, 0.22 * (1 - k / steps) ** 2)
        ctx.fill()

    # leading edge
    ctx.set_line_width(1.6)
    ctx.set_source_rgba(0.62, 0.95, 1.0, 0.95)
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(angle) * (rad - 2), cy + math.sin(angle) * (rad - 2))
    ctx.stroke()

    # blips
    blips = [(0.35, 0.62), (1.65, 0.78), (2.75, 0.45), (4.25, 0.86), (5.35, 0.30)]
    for bang, br in blips:
        phase = ((angle - bang) % (2 * math.pi)) / (2 * math.pi)
        glow = max(0.0, 1.0 - phase / 0.32)
        bx = cx + math.cos(bang) * rad * br
        by = cy + math.sin(bang) * rad * br
        ctx.set_source_rgba(0.204, 0.960, 0.720, 0.18 + 0.75 * glow)
        ctx.arc(bx, by, 2.4 + 2.6 * glow, 0, 2 * math.pi)
        ctx.fill()
        if glow > 0.15:
            ctx.set_source_rgba(0.204, 0.960, 0.720, 0.18 * glow)
            ctx.arc(bx, by, 7 + 9 * (1 - glow), 0, 2 * math.pi)
            ctx.stroke()

    # labels
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(10.5)
    label = "THREAT RADAR // "
    ext = ctx.text_extents(label)
    cx_label = cx - (ext.width + 6) / 2
    label_y = cy + rad + 26
    ctx.set_source_rgba(*rgba(CYAN, 0.65))
    ctx.move_to(cx_label, label_y)
    ctx.show_text(label)

    live = "LIVE" if (frame // 20) % 2 == 0 else "SCAN"
    ext2 = ctx.text_extents(live)
    lx = cx_label + ext.width + 6
    ctx.set_source_rgba(0.204, 0.910, 0.680, 0.95)
    if frame % 20 < 12:
        ctx.arc(lx - 5, label_y - 3.5, 2.2, 0, 2 * math.pi)
        ctx.fill()
    ctx.move_to(lx, label_y)
    ctx.show_text(live)

    # tiny corner decoration
    ctx.set_font_size(10)
    ctx.set_source_rgba(*rgba(MUTED, 0.7))
    ctx.move_to(W - 168, 40)
    ctx.show_text("SEC//OPS")
    ctx.move_to(W - 168, 58)
    ctx.show_text("SECTOR 07 · 0x1F")
    ctx.set_source_rgba(0.204, 0.910, 0.680, 0.9)
    ctx.arc(W - 180, 36, 3, 0, 2 * math.pi)
    ctx.fill()


def render(frames_dir):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for frame in range(FRAMES):
        ctx = cairo.Context(surface)
        draw_background(ctx, frame)
        draw_title(ctx, frame)
        draw_terminal(ctx, frame)
        draw_radar(ctx, frame)
        surface.write_to_png(os.path.join(frames_dir, f"frame_{frame:03d}.png"))


def build_gif(frames_dir, out_path, tmp_root):
    subprocess.run(
        [
            "magick", "-delay", str(DELAY_CS), "-loop", "0",
            os.path.join(frames_dir, "frame_*.png"),
            "-layers", "Optimize",
            "-colors", "160",
            out_path,
        ],
        check=True,
    )


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "banner.gif")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    frames_dir = tempfile.mkdtemp(prefix="banner-frames-", dir=tmp_root)
    try:
        render(frames_dir)
        build_gif(frames_dir, out, tmp_root)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    tmp_root = "/tmp/opencode"
    os.makedirs(tmp_root, exist_ok=True)
    main()
