#!/usr/bin/env python3
"""
=============================================================================
Terminal Boot-Up ASCII Profile SVG Animator
=============================================================================
Author: Expert Python & Frontend UI Hacker
Description:
    Takes a local profile photo (e.g., 'profile.jpg'), processes it using PIL
    (grayscale, contrast enhancement, aspect-ratio correction, density mapping),
    and generates a self-contained, animated SVG file ('animated_profile.svg').

    The output SVG simulates a terminal/hacker boot-up sequence where the ASCII
    art types out line-by-line from top to bottom with custom keyframe animations.

Usage:
    python3 generate_ascii_svg.py
=============================================================================
"""

import html
import os
import sys
from PIL import Image, ImageOps, ImageEnhance

# =============================================================================
# === CONFIGURATION & STYLING PARAMETERS ======================================
# =============================================================================

# Paths
INPUT_IMAGE_PATH = "profile.jpg"
OUTPUT_SVG_PATH = "animated_profile.svg"

# Dimensions & Aspect Ratio
COLUMNS = 80             # Target width in ASCII characters (70-80 recommended for READMEs)
FONT_SIZE = 11           # Font size in pixels
LINE_HEIGHT = 13         # Vertical spacing between rows in pixels
CHAR_WIDTH = 6.6         # Approximate character width in pixels for monospace 11px
FONT_ASPECT_RATIO = 0.55 # Ratio of char width to line height (~6.6 / ~13 = ~0.55)
                         # This corrects vertical stretching when resizing the photo!

# Styling & Colors
BG_COLOR = "#0D1117"     # GitHub Dark Mode background (#0D1117)
TEXT_COLOR = "#00FF99"   # Terminal Green (#00FF99) or Off-white (#F8F8F2)
FONT_FAMILY = "'Courier New', Courier, monospace"

# ASCII Density Ramps (ordered from dark/background to bright/densest)
# You can swap between these by changing DENSITY_CHARS below:
RAMP_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
RAMP_STANDARD = " .:-=+*#%@"
RAMP_BINARY   = " 01"
RAMP_CYBER    = " .-*+=#$@"

DENSITY_CHARS = RAMP_DETAILED  # Active density character map

# Image Enhancement (Helps facial features pop in ASCII format)
AUTO_CONTRAST = True     # Automatically stretch histogram to use full 0-255 range
CONTRAST_BOOST = 1.25    # Multiplier > 1.0 increases contrast sharpness

# Animation Timing (Seconds)
ANIMATION_DELAY_PER_LINE = 0.04  # Delay between each successive line appearing
ANIMATION_DURATION = 0.18        # Duration of each line's fade-in & snap animation

# Terminal Aesthetic Enhancements
SHOW_TERMINAL_HEADER = True      # Draws a macOS-style terminal title bar with window buttons
HEADER_TITLE = "antigravity@portfolio: ~/profile_matrix"
INCLUDE_BOOT_PROMPT = True       # Prepend terminal command/status lines before the ASCII art


# =============================================================================
# === IMAGE PROCESSING MODULE =================================================
# =============================================================================

def process_image_to_ascii(image_path: str, columns: int, density_chars: str) -> list[str]:
    """
    Opens the image, converts to grayscale, applies contrast adjustments,
    resizes while correcting for font aspect ratio, and maps pixel values
    to ASCII characters.
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found at '{image_path}'. Please ensure the file exists.", file=sys.stderr)
        sys.exit(1)

    print(f"[1/4] Loading image from '{image_path}'...")
    with Image.open(image_path) as img:
        # Convert to grayscale (L mode: 8-bit pixels, black and white)
        img = img.convert("L")

        # Optional: Boost contrast for sharper ASCII feature separation
        if AUTO_CONTRAST:
            img = ImageOps.autocontrast(img, cutoff=1)
        if CONTRAST_BOOST != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(CONTRAST_BOOST)

        # Calculate target height accounting for font aspect ratio
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width
        target_height = max(1, int(columns * aspect_ratio * FONT_ASPECT_RATIO))

        print(f"[2/4] Resizing from {orig_width}x{orig_height} to {columns}x{target_height} ASCII grid...")
        img = img.resize((columns, target_height), Image.Resampling.LANCZOS)

        # Map pixel intensity (0-255) to character density index
        print("[3/4] Mapping pixel densities to ASCII character ramp...")
        pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
        num_chars = len(density_chars)
        ascii_str = "".join([
            density_chars[min(num_chars - 1, int((pixel / 256.0) * num_chars))]
            for pixel in pixels
        ])

        # Split flat string into a list of individual lines
        ascii_lines = [ascii_str[i : i + columns] for i in range(0, len(ascii_str), columns)]
        return ascii_lines


# =============================================================================
# === SVG GENERATION MODULE ===================================================
# =============================================================================

def escape_xml_text(text: str) -> str:
    """Escapes XML/SVG special characters so the output is well-formed XML."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


def generate_animated_svg(ascii_lines: list[str], output_path: str) -> None:
    """
    Constructs a valid XML/SVG document containing the ASCII lines wrapped
    in <text> elements with embedded CSS keyframe animations.
    """
    print("[4/4] Generating animated SVG file...")

    # Calculate padding and header offsets
    header_height = 36 if SHOW_TERMINAL_HEADER else 0
    padding_x = 24
    padding_y = 20

    # Prepare lines to render (optional boot prompt + ASCII lines)
    render_lines = []
    current_delay = 0.0

    if INCLUDE_BOOT_PROMPT:
        render_lines.append({
            "text": f"$ ./render_profile --source {INPUT_IMAGE_PATH} --output ascii-matrix",
            "class": "line prompt",
            "delay": current_delay
        })
        current_delay += 0.40
        render_lines.append({
            "text": "[SYSTEM] Biometric matrix loaded. Booting visual stream...",
            "class": "line sys-msg",
            "delay": current_delay
        })
        current_delay += 0.40
        # Add a blank line separator
        render_lines.append({
            "text": "",
            "class": "line",
            "delay": current_delay
        })
        current_delay += 0.15

    for line_text in ascii_lines:
        render_lines.append({
            "text": line_text,
            "class": "line",
            "delay": current_delay
        })
        current_delay += ANIMATION_DELAY_PER_LINE

    total_lines = len(render_lines)
    canvas_width = int(padding_x * 2 + COLUMNS * CHAR_WIDTH)
    canvas_height = int(header_height + padding_y * 2 + total_lines * LINE_HEIGHT)

    # Build SVG content strings
    svg_parts = []

    # XML Header & SVG Root Tag
    svg_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {canvas_width} {canvas_height}" '
        f'width="100%" height="100%">'
    )

    # Embedded CSS Styling & @keyframes
    svg_parts.append('  <style>')
    svg_parts.append('    /* Base Terminal Background & Window Styling */')
    svg_parts.append(f'    .bg {{ fill: {BG_COLOR}; }}')
    svg_parts.append('    .window-header { fill: #161B22; stroke: #30363D; stroke-width: 1px; }')
    svg_parts.append('    .window-title {')
    svg_parts.append('      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;')
    svg_parts.append('      font-size: 12px; fill: #8B949E; font-weight: 600; text-anchor: middle;')
    svg_parts.append('    }')
    svg_parts.append('')
    svg_parts.append('    /* Core Line Animation & Monospace Typography */')
    svg_parts.append('    .line {')
    svg_parts.append(f'      font-family: {FONT_FAMILY};')
    svg_parts.append(f'      font-size: {FONT_SIZE}px;')
    svg_parts.append(f'      fill: {TEXT_COLOR};')
    svg_parts.append('      white-space: pre;')
    svg_parts.append('      opacity: 0;')
    svg_parts.append(f'      animation: boot-line {ANIMATION_DURATION}s ease-in forwards;')
    svg_parts.append('    }')
    svg_parts.append('')
    svg_parts.append('    /* Optional Terminal Boot Prompt Styling */')
    svg_parts.append('    .prompt { fill: #F8F8F2; font-weight: bold; }')
    svg_parts.append('    .sys-msg { fill: #8BE9FD; }')
    svg_parts.append('')
    svg_parts.append('    /* Keyframes: Fade in and snap horizontally from slight offset */')
    svg_parts.append('    @keyframes boot-line {')
    svg_parts.append('      0% {')
    svg_parts.append('        opacity: 0;')
    svg_parts.append('        transform: translateX(-4px);')
    svg_parts.append('      }')
    svg_parts.append('      100% {')
    svg_parts.append('        opacity: 1;')
    svg_parts.append('        transform: translateX(0);')
    svg_parts.append('      }')
    svg_parts.append('    }')
    svg_parts.append('  </style>')
    svg_parts.append('')

    # Background Canvas Rectangle with rounded corners
    svg_parts.append(f'  <rect class="bg" width="{canvas_width}" height="{canvas_height}" rx="10" ry="10" />')

    # Optional macOS-style Terminal Window Header Bar
    if SHOW_TERMINAL_HEADER:
        svg_parts.append(f'  <path class="window-header" d="M 0 10 Q 0 0 10 0 L {canvas_width - 10} 0 Q {canvas_width} 0 {canvas_width} 10 L {canvas_width} {header_height} L 0 {header_height} Z" />')
        # Window Control Buttons (Red, Yellow, Green)
        svg_parts.append('  <circle cx="20" cy="18" r="6" fill="#FF5F56" />')
        svg_parts.append('  <circle cx="40" cy="18" r="6" fill="#FFBD2E" />')
        svg_parts.append('  <circle cx="60" cy="18" r="6" fill="#27C93F" />')
        # Window Title
        svg_parts.append(f'  <text class="window-title" x="{canvas_width // 2}" y="22">{escape_xml_text(HEADER_TITLE)}</text>')
        svg_parts.append(f'  <line x1="0" y1="{header_height}" x2="{canvas_width}" y2="{header_height}" stroke="#30363D" stroke-width="1" />')

    # Group containing all text lines
    svg_parts.append('  <g class="terminal-content">')
    for i, item in enumerate(render_lines):
        y_pos = header_height + padding_y + (i + 1) * LINE_HEIGHT
        escaped_text = escape_xml_text(item["text"])
        delay = item["delay"]
        css_class = item["class"]
        svg_parts.append(
            f'    <text x="{padding_x}" y="{y_pos}" xml:space="preserve" '
            f'class="{css_class}" style="animation-delay: {delay:.2f}s;">{escaped_text}</text>'
        )
    svg_parts.append('  </g>')

    # Close SVG Document
    svg_parts.append('</svg>')

    # Write output to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))

    print(f"\n[SUCCESS] Generated animated terminal SVG at: '{output_path}'")
    print(f"          Total lines: {total_lines} | Total animation duration: ~{current_delay + ANIMATION_DURATION:.2f}s")


# =============================================================================
# === MAIN ENTRY POINT ========================================================
# =============================================================================

def main():
    print("=== Terminal Boot-Up ASCII Profile SVG Animator ===")
    ascii_lines = process_image_to_ascii(INPUT_IMAGE_PATH, COLUMNS, DENSITY_CHARS)
    generate_animated_svg(ascii_lines, OUTPUT_SVG_PATH)


if __name__ == "__main__":
    main()
