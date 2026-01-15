#!/usr/bin/env python3
"""
CRT IMG -> SVG (RGB subpixel stripes) for pen plotting on black paper.

Updates in this version:
- After saving, it immediately relaunches the import UI again (no “Done” popup blocking the loop).
- The import UI includes a checkbox: “Add black background” (adds a black rect behind the paths).

Dependency:
  pip install pillow
"""

import os
from dataclasses import dataclass

# --- Config you may want to tweak ---
@dataclass
class Settings:
    # Keep plot size manageable by downscaling input image if wider than this.
    max_width_px: int = 320

    # Output drawing size (mm). Height is set by image aspect ratio.
    target_width_mm: float = 260.0

    # Margin around drawing (mm)
    margin_mm: float = 6.0

    # Stroke width in mm (pen-dependent)
    stroke_width_mm: float = 0.28

    # Subpixel x offsets within a pixel (0..1 across pixel width)
    subpixel_offsets: tuple = (0.18, 0.50, 0.82)

    # Brightness -> dash density
    dash_steps: int = 9          # number of vertical "slots" per pixel stripe
    dash_fill: float = 0.70      # fraction of each slot that is ink (rest is gap)
    min_channel_cutoff: int = 6  # ignore tiny channel values to reduce clutter

    # Gamma: >1 makes mid/darks dimmer; <1 makes mid/darks brighter
    gamma: float = 1.0

SET = Settings()

def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        raise RuntimeError("Missing dependency: Pillow. Install with: pip install pillow")

def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )

def _gamma_map(v255: int) -> float:
    v = max(0, min(255, v255)) / 255.0
    if SET.gamma != 1.0:
        v = pow(v, SET.gamma)
    return v

def _add_dash_segments(path_parts, x_mm, y0_mm, y1_mm, intensity01: float):
    """
    Add distributed dash segments along the vertical stripe [y0..y1] at x.
    Uses error-accumulation to distribute "on" slots evenly.
    """
    if intensity01 <= 0.0:
        return

    total_len = y1_mm - y0_mm
    steps = max(1, int(SET.dash_steps))
    slot = total_len / steps

    on_slots = int(round(intensity01 * steps))
    if on_slots <= 0:
        return
    if on_slots >= steps:
        path_parts.append(f"M {x_mm:.4f} {y0_mm:.4f} L {x_mm:.4f} {y1_mm:.4f}")
        return

    err = 0
    for i in range(steps):
        err += on_slots
        if err >= steps:
            err -= steps
            slot_top = y0_mm + i * slot
            dash_len = slot * float(SET.dash_fill)
            y_a = slot_top + (slot - dash_len) * 0.5
            y_b = y_a + dash_len
            path_parts.append(f"M {x_mm:.4f} {y_a:.4f} L {x_mm:.4f} {y_b:.4f}")

def image_to_crt_svg(image_path: str, svg_path: str, add_black_bg: bool):
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    # Downscale to keep plotting reasonable
    if w > SET.max_width_px:
        scale = SET.max_width_px / float(w)
        new_w = SET.max_width_px
        new_h = max(1, int(round(h * scale)))
        img = img.resize((new_w, new_h), Image.LANCZOS)
        w, h = img.size

    # Pixel size (mm) based on target width
    px_w = SET.target_width_mm / float(w)
    px_h = px_w  # square pixels

    out_w_mm = SET.margin_mm * 2.0 + w * px_w
    out_h_mm = SET.margin_mm * 2.0 + h * px_h

    path_r, path_g, path_b = [], [], []

    # Raster scan: top->bottom rows, left->right columns
    pix = img.load()
    for y in range(h):
        y0 = SET.margin_mm + y * px_h
        y1 = y0 + px_h

        for x in range(w):
            r, g, b = pix[x, y]
            if r < SET.min_channel_cutoff and g < SET.min_channel_cutoff and b < SET.min_channel_cutoff:
                continue

            x_base = SET.margin_mm + x * px_w
            xs = (
                x_base + SET.subpixel_offsets[0] * px_w,
                x_base + SET.subpixel_offsets[1] * px_w,
                x_base + SET.subpixel_offsets[2] * px_w,
            )

            ir = _gamma_map(r)
            ig = _gamma_map(g)
            ib = _gamma_map(b)

            if r >= SET.min_channel_cutoff:
                _add_dash_segments(path_r, xs[0], y0, y1, ir)
            if g >= SET.min_channel_cutoff:
                _add_dash_segments(path_g, xs[1], y0, y1, ig)
            if b >= SET.min_channel_cutoff:
                _add_dash_segments(path_b, xs[2], y0, y1, ib)

    title = os.path.basename(image_path)
    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{out_w_mm:.3f}mm" height="{out_h_mm:.3f}mm" '
        f'viewBox="0 0 {out_w_mm:.6f} {out_h_mm:.6f}">'
    )
    svg.append(f"<title>{_escape(title)} CRT raster RGB</title>")

    if add_black_bg:
        svg.append(f'<rect x="0" y="0" width="{out_w_mm:.6f}" height="{out_h_mm:.6f}" fill="black"/>')

    common = f'fill="none" stroke-linecap="round" stroke-width="{SET.stroke_width_mm:.3f}"'

    def emit_group(color_name, stroke, path_parts):
        if not path_parts:
            return
        d = " ".join(path_parts)
        svg.append(f'<g id="{color_name}" {common} stroke="{stroke}">')
        svg.append(f'  <path d="{d}"/>')
        svg.append("</g>")

    emit_group("red",   "rgb(255,0,0)", path_r)
    emit_group("green", "rgb(0,255,0)", path_g)
    emit_group("blue",  "rgb(0,0,255)", path_b)

    svg.append("</svg>")

    os.makedirs(os.path.dirname(os.path.abspath(svg_path)), exist_ok=True)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

# ---------------- UI ----------------

def import_dialog_with_bg_checkbox():
    """
    Small Tk window that includes:
      - Checkbox: Add black background
      - Button: Choose image...
      - Button: Cancel
    Returns (image_path or None, add_black_bg_bool)
    """
    import tkinter as tk
    from tkinter import filedialog

    result = {"path": None, "bg": False}

    root = tk.Tk()
    root.title("SCANLINE FILTER")
    root.resizable(False, False)

    bg_var = tk.BooleanVar(value=True)

    frame = tk.Frame(root, padx=14, pady=12)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text="Choose an image to convert.\nEach pixel becomes RGB subpixel stripes.",
        justify="left"
    ).pack(anchor="w")

    tk.Checkbutton(
        frame,
        text="Add black background (for preview)",
        variable=bg_var
    ).pack(anchor="w", pady=(10, 10))

    btn_row = tk.Frame(frame)
    btn_row.pack(fill="x")

    def choose():
        path = filedialog.askopenfilename(
            title="Select JPG/PNG image",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            result["path"] = path
            result["bg"] = bool(bg_var.get())
            root.destroy()

    def cancel():
        result["path"] = None
        result["bg"] = bool(bg_var.get())
        root.destroy()

    tk.Button(btn_row, text="Choose Image…", command=choose, width=16).pack(side="left")
    tk.Button(btn_row, text="Cancel", command=cancel, width=10).pack(side="right")

    # Make Enter choose, Esc cancel
    root.bind("<Return>", lambda e: choose())
    root.bind("<Escape>", lambda e: cancel())

    root.mainloop()
    return result["path"], result["bg"]

def save_dialog(suggest_name):
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.update()

    path = filedialog.asksaveasfilename(
        title="Save SVG",
        defaultextension=".svg",
        initialfile=suggest_name,
        filetypes=[("SVG", "*.svg")],
    )
    root.destroy()
    return path or None

def error_box(title, msg):
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    root.update()
    messagebox.showerror(title, msg)
    root.destroy()

def main():
    _require_pillow()

    while True:
        img_path, add_bg = import_dialog_with_bg_checkbox()
        if not img_path:
            return  # user cancelled

        base = os.path.splitext(os.path.basename(img_path))[0]
        suggest = f"{base}_CRT_RGB.svg"
        svg_path = save_dialog(suggest)

        # If user cancels save, go right back to import UI
        if not svg_path:
            continue

        try:
            image_to_crt_svg(img_path, svg_path, add_bg)
            # IMPORTANT: no “Done” popup, so it immediately relaunches (loop continues)
        except Exception as e:
            error_box("Error", f"{type(e).__name__}: {e}")
            # then relaunch import UI automatically

if __name__ == "__main__":
    main()
