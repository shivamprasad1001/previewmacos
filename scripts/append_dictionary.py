#!/usr/bin/env python3
"""Adds supplemental code-verified entries to dictionary.json to guarantee 100% test coverage."""

import json
import os

extra_entries = [
    {
        "id": "align-center",
        "name": "Align Center",
        "letter": "A",
        "meaning": "Centers text lines horizontally within active text annotation boxes.",
        "where": "Markup Toolbar > Text Alignment Dropdown > Align Center",
        "steps": [
            "Select a text box on canvas.",
            "Click the Text Alignment dropdown on Markup Toolbar.",
            "Select Align Center."
        ],
        "shortcut": "",
        "related": ["align-left", "align-right", "text-box-tool"]
    },
    {
        "id": "align-left",
        "name": "Align Left",
        "letter": "A",
        "meaning": "Aligns text lines to the left margin within text annotation boxes.",
        "where": "Markup Toolbar > Text Alignment Dropdown > Align Left",
        "steps": [
            "Select a text box on canvas.",
            "Click the Text Alignment dropdown on Markup Toolbar.",
            "Select Align Left."
        ],
        "shortcut": "",
        "related": ["align-center", "align-right", "text-box-tool"]
    },
    {
        "id": "align-right",
        "name": "Align Right",
        "letter": "A",
        "meaning": "Aligns text lines to the right margin within text annotation boxes.",
        "where": "Markup Toolbar > Text Alignment Dropdown > Align Right",
        "steps": [
            "Select a text box on canvas.",
            "Click the Text Alignment dropdown on Markup Toolbar.",
            "Select Align Right."
        ],
        "shortcut": "",
        "related": ["align-left", "align-center", "text-box-tool"]
    },
    {
        "id": "apply-permanent-redactions",
        "name": "Apply Permanent Redactions",
        "letter": "A",
        "meaning": "Permanently scrubs redacted pixels and underlying text bytes from the file.",
        "where": "Edit > Apply All Redactions or Canvas Redaction Menu",
        "steps": [
            "Mark redaction boxes over sensitive text.",
            "Select Edit > Apply All Redactions.",
            "Confirm the irreversible sanitization prompt."
        ],
        "shortcut": "",
        "related": ["redaction-tool", "apply-all-redactions"]
    },
    {
        "id": "copy-current-page-text",
        "name": "Copy Current Page Text",
        "letter": "C",
        "meaning": "Extracts and copies all textual words on active page to clipboard.",
        "where": "Canvas Context Menu > Copy Page Text",
        "steps": [
            "Right-click any empty area on canvas.",
            "Select Copy Page Text.",
            "Paste into external text editors."
        ],
        "shortcut": "",
        "related": ["copy-text", "extract-all-text"]
    },
    {
        "id": "exit-slideshow",
        "name": "Exit Slideshow",
        "letter": "E",
        "meaning": "Leaves full-screen presentation mode and restores the standard window.",
        "where": "Slideshow Overlay or Press Esc",
        "steps": [
            "Press Esc while in slideshow mode.",
            "The application returns to normal window view."
        ],
        "shortcut": "Esc",
        "related": ["slideshow-mode", "start-slideshow"]
    },
    {
        "id": "extract-all-text-clipboard",
        "name": "Extract All Text to Clipboard",
        "letter": "E",
        "meaning": "Copies text across all pages in the document to system clipboard.",
        "where": "Edit > Extract All Text to File... or Canvas Context Menu",
        "steps": [
            "Select Edit > Extract All Text to File...",
            "Save text to disk or copy directly."
        ],
        "shortcut": "",
        "related": ["extract-all-text", "copy-text"]
    },
    {
        "id": "font-family",
        "name": "Font Family",
        "letter": "F",
        "meaning": "Selects typography typeface family for active text annotation boxes.",
        "where": "Markup Toolbar > Font Family Combobox",
        "steps": [
            "Select a text box on canvas.",
            "Click the Font Family dropdown on Markup Toolbar.",
            "Choose an installed system font like Inter or SF Pro."
        ],
        "shortcut": "",
        "related": ["font-size", "text-box-tool"]
    },
    {
        "id": "font-size",
        "name": "Font Size",
        "letter": "F",
        "meaning": "Sets font point size from 8 pt up to 72 pt for text annotations.",
        "where": "Markup Toolbar > Font Size Spinbox",
        "steps": [
            "Select a text box on canvas.",
            "Adjust the Font Size spinbox on Markup Toolbar.",
            "Text size scales immediately."
        ],
        "shortcut": "",
        "related": ["font-family", "text-box-tool"]
    },
    {
        "id": "open-document-or-images",
        "name": "Open Document or Images",
        "letter": "O",
        "meaning": "Primary open action loading supported PDF documents or raster graphics.",
        "where": "Top Toolbar > Open Button or File > Open...",
        "steps": [
            "Click the Open button on the top toolbar.",
            "Select files and click Open."
        ],
        "shortcut": "Ctrl + O",
        "related": ["open-file", "open-folder-images"]
    },
    {
        "id": "open-options",
        "name": "Open Options",
        "letter": "O",
        "meaning": "Dropdown menu next to Open button providing single file or folder loading.",
        "where": "Top Toolbar > Open Segmented Dropdown Arrow",
        "steps": [
            "Click the small arrow next to the Open toolbar button.",
            "Choose Open File(s)... or Open Folder of Images..."
        ],
        "shortcut": "",
        "related": ["open-file", "open-folder-images"]
    },
    {
        "id": "pause-resume-auto-advance",
        "name": "Pause / Resume Auto-advance",
        "letter": "P",
        "meaning": "Pauses or resumes automatic timed slide advancement during presentations.",
        "where": "Slideshow Mode Toolbar or Press Space",
        "steps": [
            "Start slideshow by pressing F5.",
            "Press Spacebar to pause or resume timer."
        ],
        "shortcut": "Space",
        "related": ["slideshow-mode", "exit-slideshow"]
    },
    {
        "id": "rotate-90-clockwise",
        "name": "Rotate 90° Clockwise",
        "letter": "R",
        "meaning": "Rotates current page or selected thumbnail 90 degrees clockwise.",
        "where": "Sidebar Thumbnail Context Menu > Rotate 90° Clockwise",
        "steps": [
            "Right-click any thumbnail card in the sidebar.",
            "Select Rotate 90° Clockwise.",
            "Page rotates in document structure."
        ],
        "shortcut": "Ctrl + R",
        "related": ["rotate-90-counter-clockwise", "rotate-right"]
    },
    {
        "id": "rotate-90-counter-clockwise",
        "name": "Rotate 90° Counter-Clockwise",
        "letter": "R",
        "meaning": "Rotates current page or selected thumbnail 90 degrees counter-clockwise.",
        "where": "Sidebar Thumbnail Context Menu > Rotate 90° Counter-Clockwise",
        "steps": [
            "Right-click any thumbnail card in the sidebar.",
            "Select Rotate 90° Counter-Clockwise.",
            "Page rotates in document structure."
        ],
        "shortcut": "Ctrl + L",
        "related": ["rotate-90-clockwise", "rotate-left"]
    },
    {
        "id": "rotate-left-90",
        "name": "Rotate Left 90°",
        "letter": "R",
        "meaning": "Rotates current canvas view 90 degrees counter-clockwise.",
        "where": "Markup Toolbar > Rotate Left Button",
        "steps": [
            "Click the Rotate Left button on Markup Toolbar.",
            "Or press Ctrl + L."
        ],
        "shortcut": "Ctrl + L",
        "related": ["rotate-left", "rotate-right"]
    },
    {
        "id": "rotate-selection-90",
        "name": "Rotate Selection 90°",
        "letter": "R",
        "meaning": "Rotates active marquee crop area 90 degrees clockwise.",
        "where": "Markup Toolbar > Rotate Selection Button",
        "steps": [
            "Draw a selection marquee on canvas.",
            "Click the Rotate Selection button or press Ctrl + R."
        ],
        "shortcut": "Ctrl + R",
        "related": ["rotate-selection", "crop-selection"]
    },
    {
        "id": "selection-tools",
        "name": "Selection Tools",
        "letter": "S",
        "meaning": "Dropdown offering Rectangular, Oval, and Lasso selection marquee modes.",
        "where": "Markup Toolbar > Selection Dropdown",
        "steps": [
            "Click the Selection dropdown on Markup Toolbar.",
            "Choose Rectangular, Oval, or Lasso Selection.",
            "Drag on canvas to frame an area."
        ],
        "shortcut": "",
        "related": ["rectangular-selection", "oval-selection", "lasso-selection"]
    },
    {
        "id": "shapes",
        "name": "Shapes",
        "letter": "S",
        "meaning": "Dropdown menu providing Rectangle, Rounded Rectangle, Oval, Line, and Arrow tools.",
        "where": "Markup Toolbar > Shapes Button",
        "steps": [
            "Click the Shapes button on Markup Toolbar.",
            "Pick Rectangle, Rounded Rectangle, Oval, Line, or Arrow.",
            "Drag on canvas to place the vector shape."
        ],
        "shortcut": "",
        "related": ["rectangle-shape", "ellipse-oval-shape", "arrow-tool"]
    },
    {
        "id": "show-colors",
        "name": "Show Colors...",
        "letter": "S",
        "meaning": "Opens full system color picker dialog for custom stroke and fill colors.",
        "where": "Stroke or Fill Color Dropdown > Show Colors...",
        "steps": [
            "Click Stroke Color or Fill Color dropdown.",
            "Click Show Colors... at the bottom.",
            "Pick any hue, saturation, and luminance."
        ],
        "shortcut": "",
        "related": ["border-stroke-color", "fill-color"]
    },
    {
        "id": "show-menu-bar",
        "name": "Show Menu Bar",
        "letter": "S",
        "meaning": "Shows or hides the top application menubar for compact viewing.",
        "where": "View > Toggle Menu Bar",
        "steps": [
            "Select View > Toggle Menu Bar.",
            "Menubar toggles between visible and hidden."
        ],
        "shortcut": "",
        "related": ["toggle-status-bar", "window-overview"]
    },
    {
        "id": "show-status-bar",
        "name": "Show Status Bar",
        "letter": "S",
        "meaning": "Displays bottom bar containing zoom percentage and page count details.",
        "where": "View > Toggle Status Bar",
        "steps": [
            "Select View > Toggle Status Bar.",
            "Status bar toggles visible or hidden."
        ],
        "shortcut": "",
        "related": ["toggle-status-bar", "window-overview"]
    },
    {
        "id": "start-slideshow",
        "name": "Start Slideshow",
        "letter": "S",
        "meaning": "Launches full-screen black-background slideshow presentation mode.",
        "where": "View > Slideshow Mode or Press F5",
        "steps": [
            "Select View > Slideshow Mode.",
            "Use arrow keys to navigate slides.",
            "Press Esc to exit."
        ],
        "shortcut": "F5",
        "related": ["slideshow-mode", "exit-slideshow"]
    },
    {
        "id": "text-alignment-quick-styles",
        "name": "Text Alignment & Quick Styles",
        "letter": "T",
        "meaning": "Dropdown menu offering left, center, right alignment and quick point sizes.",
        "where": "Markup Toolbar > Text Alignment Dropdown (A)",
        "steps": [
            "Select any text annotation box.",
            "Click the A dropdown on the Markup Toolbar.",
            "Choose text alignment or quick font sizes."
        ],
        "shortcut": "",
        "related": ["align-left", "align-center", "align-right"]
    },
    {
        "id": "toggle-dark-light-mode",
        "name": "Toggle Dark/Light Mode",
        "letter": "T",
        "meaning": "Switches the active application visual appearance between Dark and Light mode.",
        "where": "Top Toolbar > Theme Button or Apple Menu > Toggle Dark/Light Theme",
        "steps": [
            "Click the sun/moon button on the top toolbar.",
            "Or press Ctrl + T."
        ],
        "shortcut": "Ctrl + T",
        "related": ["dark-light-theme-toggle", "preferences"]
    },
    {
        "id": "two-pages-two-up",
        "name": "Two Pages (Two-Up)",
        "letter": "T",
        "meaning": "Displays document in two-page facing spread layout matching book pages.",
        "where": "View > PDF View Mode > Two Pages Continuous (Two-Up)",
        "steps": [
            "Select View > PDF View Mode > Two Pages Continuous (Two-Up).",
            "Pages display side by side on canvas."
        ],
        "shortcut": "",
        "related": ["two-pages-continuous-view", "single-page-view"]
    },
    {
        "id": "zoom-maximize",
        "name": "Zoom / Maximize",
        "letter": "Z",
        "meaning": "Toggles the window between standard size and full desktop workspace.",
        "where": "Window > Zoom / Maximize or Green Traffic Light Button",
        "steps": [
            "Select Window > Zoom / Maximize.",
            "Window toggles maximized state."
        ],
        "shortcut": "",
        "related": ["minimize-window", "frameless-window-mode"]
    },
    {
        "id": "macos-frameless-window",
        "name": "macOS Frameless Window",
        "letter": "M",
        "meaning": "Removes native window decorations for clean macOS integrated appearance.",
        "where": "View > Frameless Window Mode",
        "steps": [
            "Select View > Frameless Window Mode or press F11.",
            "Window border toggles seamlessly."
        ],
        "shortcut": "F11",
        "related": ["frameless-window-mode", "traffic-light-buttons"]
    }
]

dict_path = "help/content/dictionary.json"
with open(dict_path, "r", encoding="utf-8") as f:
    data = json.load(f)

existing = data.get("entries", [])
existing_ids = {e["id"] for e in existing}

for ne in extra_entries:
    if ne["id"] not in existing_ids:
        existing.append(ne)

existing.sort(key=lambda e: e["name"].lower())

with open(dict_path, "w", encoding="utf-8") as f:
    json.dump({"total": len(existing), "entries": existing}, f, indent=2)

print(f"Dictionary updated with {len(existing)} entries.")
