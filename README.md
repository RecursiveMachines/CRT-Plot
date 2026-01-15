# CRT-Plot
A tiny Python tool that converts a JPG (or any image) into an SVG made of CRT-style raster “beam” lines.
Built specifically for pen plotting with only three gel pens: Red, Green, Blue (no blended colors). Perfect for RGB subpixel / scanline aesthetics on black paper.
What it makes

The SVG is drawn row-by-row like a TV raster scan
  Each pixel becomes three vertical subpixel stripes: R | G | B
  Brightness is represented by dash density:
  bright → more solid ink
  dim → dotted / sparse segments
  Output uses only three stroke colors: rgb(255,0,0), rgb(0,255,0), rgb(0,0,255)

  How it works

Launch the script
A dialog opens immediately:
Choose an image
Optional checkbox: Add black background
Choose where to save the SVG
It loops back to the import dialog so you can batch-convert multiple images

Requirements
Python 3
Pillow


pip install pillow

Run
python3 CRT-Plot.py

Plotting Tips



Use black paper for the classic CRT glow vibe
Plot one color at a time (R, then G, then B) for best registration


Customization

Inside the script you can tweak:
stroke_width_mm → pen line thickness

dash_steps, dash_fill → how “CRT” the brightness dithering looks

gamma → brightness curve
