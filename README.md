# CRT-Plot

**CRT-Plot** converts an image (JPG/PNG) into an SVG made of **CRT-style raster line segments** for **pen plotting** using **only three pens**: **Red, Green, Blue**.

It draws the image **row-by-row like a TV scan**, and each pixel is represented as **three vertical “subpixel” stripes**: **R | G | B**. Brightness is encoded as **dash density** (solid for bright, sparse/dotted for dim) so the output remains strictly **RGB-only** with no blended stroke colors.

## Features

- **RGB subpixel rendering**: every pixel becomes three vertical stripes (R, G, B)
- **Raster scan order**: processes left-to-right, top-to-bottom like a CRT beam
- **Brightness via dash density**: more ink for brighter values, less for darker values
- **Optional black background**: checkbox in the import dialog to add a black rectangle behind the plot
- **Fast batch workflow**: after exporting, the import dialog opens again

## Output

- SVG groups are organized by color:
  - `id="red"`
  - `id="green"`
  - `id="blue"`
- Strokes use:
  - `rgb(255,0,0)`, `rgb(0,255,0)`, `rgb(0,0,255)`

## Requirements

- Python 3
- Pillow

Install:

```bash
pip install pillow
```

## Run

```bash
python3 CRT-Plot.py
```

## Plotting notes

- For the classic CRT look, plot on **black paper** with **red/green/blue gel pens**.
- For best results, plot **one color at a time** (R, then G, then B) for cleaner registration.
- Complexity grows quickly with resolution—if plots are too dense, reduce the maximum width in settings.

## Configuration

Edit the settings near the top of `CRT-Plot.py` to tune the look and plot time:

- `max_width_px` — downscales large images to keep SVGs manageable
- `target_width_mm` — output width in mm (height follows aspect)
- `stroke_width_mm` — pen line width
- `dash_steps`, `dash_fill` — dash “density” used for brightness
- `gamma` — brightness curve

