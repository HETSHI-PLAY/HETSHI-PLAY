#!/usr/bin/env python3
"""
Convert the short clips in image/ into README-ready GIFs with a
SOC-flavoured overlay, in a style consistent with assets/banner.gif.

Requires: pycairo, ffmpeg. Run from the repo root:
    python3 assets/make_video_gifs.py
"""

import os
import subprocess
import tempfile

import cairo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "image")
OUT = os.path.join(ROOT, "assets")
WORK = "/tmp/opencode/vidwork"

FONT = "DejaVu Sans Mono"
CYAN = (0.133, 0.827, 0.933)
GREEN = (0.204, 0.960, 0.720)
TEXT = (0.929, 0.949, 0.973)
MUTED = (0.580, 0.639, 0.722)


def spaced(ctx, x, y, text, spacing):
    ctx.move_to(x, y)
    for ch in text:
        ctx.show_text(ch)
        x += ctx.text_extents(ch).x_advance + spacing
        ctx.move_to(x, y)


def gradient_band(ctx, w, h, top, bottom_alpha=0.94):
    g = cairo.LinearGradient(0, top, 0, h)
    g.add_color_stop_rgba(0, 0.012, 0.031, 0.063, 0)
    g.add_color_stop_rgba(1, 0.012, 0.031, 0.063, bottom_alpha)
    ctx.set_source(g)
    ctx.rectangle(0, top, w, h - top)
    ctx.fill()


def hero_overlay(path):
    w, h = 1280, 720
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(s)

    gradient_band(ctx, w, h, 470)

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(13)
    ctx.set_source_rgba(*MUTED, 0.95)
    spaced(ctx, 54, 566, "// PROFILE", 2.4)

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(68)
    ctx.set_source_rgba(*TEXT, 1)
    ctx.move_to(52, 634)
    ctx.show_text("HETSHI-PLAY")

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(16)
    ctx.set_source_rgba(*CYAN, 1)
    spaced(ctx, 56, 670, "SOC  ·  BLUE TEAM  ·  CTF", 3.0)

    ctx.set_font_size(13)
    ctx.set_source_rgba(*MUTED, 0.95)
    ctx.move_to(56, 698)
    ctx.show_text("powered by caffeine and anime")

    # status pill, top right
    ctx.set_source_rgba(0.031, 0.055, 0.098, 0.72)
    ctx.rectangle(1010, 28, 222, 34)
    ctx.fill_preserve()
    ctx.set_source_rgba(*CYAN, 0.35)
    ctx.set_line_width(1)
    ctx.stroke()
    ctx.set_source_rgba(*GREEN, 1)
    ctx.arc(1028, 45, 4, 0, 6.2832)
    ctx.fill()
    ctx.set_source_rgba(*MUTED, 1)
    ctx.set_font_size(12)
    ctx.move_to(1042, 50)
    spaced(ctx, 1042, 50, "STATUS: HUNTING", 1.6)

    s.write_to_png(path)


def wink_overlay(path):
    w, h = 800, 600
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(s)

    gradient_band(ctx, w, h, 496, 0.92)

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12)
    ctx.set_source_rgba(*CYAN, 1)
    ctx.move_to(28, 540)
    ctx.show_text("$ tail -f /var/log/false-positive.log")

    ctx.set_font_size(21)
    ctx.set_source_rgba(*TEXT, 1)
    ctx.move_to(28, 574)
    ctx.show_text("POV: no alerts today")

    s.write_to_png(path)


def glitch_overlay(path):
    w, h = 640, 360
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(s)

    gradient_band(ctx, w, h, 266, 0.92)

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(17)
    ctx.set_source_rgba(*TEXT, 1)
    ctx.move_to(20, 322)
    ctx.show_text("3 AM  ·  200 alerts  ·  1 coffee")

    ctx.set_font_size(11)
    ctx.set_source_rgba(*CYAN, 1)
    ctx.move_to(20, 342)
    ctx.show_text("[ok] vibes stable, sleep not found")

    s.write_to_png(path)


def run(cmd):
    subprocess.run(cmd, check=True)


def build(src, overlay, out, fps, size):
    base = os.path.splitext(os.path.basename(src))[0]
    tmp = os.path.join(WORK, base)
    os.makedirs(tmp, exist_ok=True)
    pp = os.path.join(tmp, "pp.mp4")
    ov = os.path.join(tmp, "ov.mp4")
    pal = os.path.join(tmp, "pal.png")

    # ping-pong so the very short clips loop smoothly
    run([
        "ffmpeg", "-y", "-v", "error", "-i", src,
        "-filter_complex",
        "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[out]",
        "-map", "[out]", "-an", pp,
    ])
    run([
        "ffmpeg", "-y", "-v", "error", "-i", pp, "-i", overlay,
        "-filter_complex", "[0:v][1:v]overlay=0:0",
        "-an", ov,
    ])
    chain = f"fps={fps},scale={size}:flags=lanczos"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", ov,
        "-vf", f"{chain},palettegen=max_colors=64:stats_mode=diff", pal,
    ])
    run([
        "ffmpeg", "-y", "-v", "error", "-i", ov, "-i", pal,
        "-lavfi", f"[0:v]{chain}[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle",
        "-loop", "0", out,
    ])
    print(f"{os.path.basename(out):18} {os.path.getsize(out) / 1024:7.0f} KB")


def main():
    os.makedirs(WORK, exist_ok=True)

    hero_ov = os.path.join(WORK, "hero_overlay.png")
    wink_ov = os.path.join(WORK, "wink_overlay.png")
    glitch_ov = os.path.join(WORK, "glitch_overlay.png")
    hero_overlay(hero_ov)
    wink_overlay(wink_ov)
    glitch_overlay(glitch_ov)

    build(
        os.path.join(SRC, "ssstwitter.com_1794142180042.mp4"),
        hero_ov,
        os.path.join(OUT, "hero.gif"),
        20, "900:506",
    )
    build(
        os.path.join(SRC, "ssstwitter.com_1794142198947.mp4"),
        wink_ov,
        os.path.join(OUT, "wink.gif"),
        10, "480:360",
    )
    build(
        os.path.join(SRC, "ssstwitter.com_1794142029622.mp4"),
        glitch_ov,
        os.path.join(OUT, "alerts.gif"),
        15, "640:360",
    )


if __name__ == "__main__":
    main()
