#!/usr/bin/env python3
"""Builds the complete Help Dictionary adhering to strict writing rules."""

import json
import os

entries = [
    # A
    {
        "id": "about-document-viewer",
        "name": "About Document Viewer",
        "letter": "A",
        "meaning": "Displays application version, developer credits, and update links.",
        "where": "Apple Menu > About Document Viewer or Help > About Document Viewer",
        "steps": [
            "Click the Apple Menu or Help Menu.",
            "Select About Document Viewer.",
            "Review version information or click Check for Updates..."
        ],
        "shortcut": "",
        "related": ["check-for-updates", "what-is-preview"]
    },
    {
        "id": "actual-size",
        "name": "Actual Size",
        "letter": "A",
        "meaning": "Displays the document at 100 percent scale matching original pixel dimensions.",
        "where": "View > Actual Size or Canvas Context Menu > Actual Size",
        "steps": [
            "Open any document or image.",
            "Select View > Actual Size or press Ctrl + 0.",
            "Scroll or pan to inspect details at 1:1 pixel resolution."
        ],
        "shortcut": "Ctrl + 0",
        "related": ["zoom-to-fit", "zoom-in", "zoom-out"]
    },
    {
        "id": "adjust-color",
        "name": "Adjust Color",
        "letter": "A",
        "meaning": "Fine-tunes image exposure, contrast, saturation, temperature, tint, and sharpness.",
        "where": "Tools > Adjust Color... or Markup Toolbar > Adjust Color",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag sliders to adjust tone or click Auto Levels.",
            "Click Done to apply changes or click Revert."
        ],
        "shortcut": "Ctrl + Alt + C",
        "related": ["adjust-size", "auto-levels", "crop-selection"]
    },
    {
        "id": "adjust-size",
        "name": "Adjust Size",
        "letter": "A",
        "meaning": "Resizes image pixel dimensions and changes dots-per-inch print resolution.",
        "where": "Tools > Adjust Size... or Markup Toolbar > Adjust Size",
        "steps": [
            "Select Tools > Adjust Size... or press Ctrl + Alt + S.",
            "Enter target dimensions in pixels or percentage.",
            "Click OK to resize the image."
        ],
        "shortcut": "Ctrl + Alt + S",
        "related": ["adjust-color", "crop-selection", "export-dialog"]
    },
    {
        "id": "apply-all-redactions",
        "name": "Apply All Redactions",
        "letter": "A",
        "meaning": "Permanently burns black redaction boxes into document pages, destroying covered data.",
        "where": "Edit > Apply All Redactions",
        "steps": [
            "Draw black redaction boxes over sensitive text.",
            "Select Edit > Apply All Redactions.",
            "Click Yes to confirm permanent data removal."
        ],
        "shortcut": "",
        "related": ["redaction-tool", "save", "password-and-encryption"]
    },
    {
        "id": "arrow-tool",
        "name": "Arrow Tool",
        "letter": "A",
        "meaning": "Draws directional vector arrows to highlight key areas on canvas.",
        "where": "Markup Toolbar > Shapes Dropdown > Arrow",
        "steps": [
            "Click the Markup button on the top toolbar.",
            "Click the Shapes dropdown and select Arrow.",
            "Drag on the canvas from start to arrowhead endpoint."
        ],
        "shortcut": "",
        "related": ["line-tool", "shapes-dropdown", "annotate-and-markup"]
    },
    {
        "id": "auto-levels",
        "name": "Auto Levels",
        "letter": "A",
        "meaning": "Automatically optimizes tonal balance and contrast distribution for images.",
        "where": "Adjust Color Panel > Auto Levels",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Click the Auto Levels button.",
            "Click Done to accept the adjusted balance."
        ],
        "shortcut": "",
        "related": ["adjust-color", "reset-all-color", "exposure-slider"]
    },

    # B
    {
        "id": "bold-text",
        "name": "Bold Text",
        "letter": "B",
        "meaning": "Toggles bold typography styling for selected text annotation boxes.",
        "where": "Markup Toolbar > Bold (B) Button",
        "steps": [
            "Select a text annotation box on the canvas.",
            "Click the B button on the Markup Toolbar.",
            "Type your formatted text."
        ],
        "shortcut": "Ctrl + B",
        "related": ["italic-text", "underline-text", "text-box-tool"]
    },
    {
        "id": "border-stroke-color",
        "name": "Border / Stroke Color",
        "letter": "B",
        "meaning": "Sets outline stroke color for shapes, sketches, and text borders.",
        "where": "Markup Toolbar > Border / Stroke Color Dropdown",
        "steps": [
            "Click the Border / Stroke Color dropdown on the Markup Toolbar.",
            "Select any curated swatch like Red, Blue, or Black.",
            "Choose Show Colors... for full system color palette."
        ],
        "shortcut": "",
        "related": ["fill-color", "line-style-thickness", "pen-tool"]
    },

    # C
    {
        "id": "check-for-updates",
        "name": "Check for Updates",
        "letter": "C",
        "meaning": "Checks GitHub releases for new versions and downloads updates.",
        "where": "Apple Menu > Check for Updates... or Help > Check for Updates...",
        "steps": [
            "Select Check for Updates... from Apple or Help menu.",
            "Read release notes in the update window.",
            "Click Download & Install to update."
        ],
        "shortcut": "",
        "related": ["about-document-viewer", "update-banner"]
    },
    {
        "id": "clear-recent-menu",
        "name": "Clear Recent Menu",
        "letter": "C",
        "meaning": "Clears the saved history of recently opened documents from settings.",
        "where": "File > Open Recent > Clear Menu",
        "steps": [
            "Open the File menu.",
            "Hover over Open Recent.",
            "Click Clear Menu at the bottom of the list."
        ],
        "shortcut": "",
        "related": ["open-recent", "open-file"]
    },
    {
        "id": "close-window",
        "name": "Close Window",
        "letter": "C",
        "meaning": "Closes current window and prompts to save if edits are unsaved.",
        "where": "File > Close Window or Red Traffic Light Button",
        "steps": [
            "Select File > Close Window or press Ctrl + W.",
            "Click Save, Don't Save, or Cancel if prompted."
        ],
        "shortcut": "Ctrl + W",
        "related": ["save-changes-prompt", "quit-document-viewer"]
    },
    {
        "id": "contact-sheet-view",
        "name": "Contact Sheet View",
        "letter": "C",
        "meaning": "Displays document pages in a multi-column visual grid layout.",
        "where": "Sidebar Header Dropdown > Contact Sheet",
        "steps": [
            "Click the Sidebar button on toolbar to open the sidebar.",
            "Click the view dropdown at the top of the sidebar.",
            "Select Contact Sheet to browse pages in a grid."
        ],
        "shortcut": "",
        "related": ["thumbnails-view", "table-of-contents-view", "sidebar"]
    },
    {
        "id": "contrast-slider",
        "name": "Contrast Slider",
        "letter": "C",
        "meaning": "Increases or decreases contrast separation between light and dark tones.",
        "where": "Adjust Color Panel > Contrast Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Contrast slider left or right.",
            "Click Done to apply your changes."
        ],
        "shortcut": "",
        "related": ["adjust-color", "exposure-slider", "auto-levels"]
    },
    {
        "id": "copy-text",
        "name": "Copy Text",
        "letter": "C",
        "meaning": "Copies selected document text or entire page text to system clipboard.",
        "where": "Edit > Copy Text or Canvas Context Menu > Copy Selection",
        "steps": [
            "Drag over document text with your mouse to select it.",
            "Select Edit > Copy Text or press Ctrl + C.",
            "Paste the text into any target application."
        ],
        "shortcut": "Ctrl + C",
        "related": ["extract-all-text", "search-field"]
    },
    {
        "id": "crop-selection",
        "name": "Crop Selection",
        "letter": "C",
        "meaning": "Trims document boundaries to the active rectangular, oval, or lasso marquee.",
        "where": "Tools > Crop or Markup Toolbar > Crop Selection Button",
        "steps": [
            "Select Rectangular, Oval, or Lasso from the Selection dropdown.",
            "Drag across the canvas to frame the desired area.",
            "Select Tools > Crop or press Ctrl + K."
        ],
        "shortcut": "Ctrl + K",
        "related": ["rectangular-selection", "oval-selection", "lasso-selection"]
    },

    # D
    {
        "id": "dark-light-theme-toggle",
        "name": "Dark / Light Theme Toggle",
        "letter": "D",
        "meaning": "Switches the entire interface between macOS Dark mode and Light mode.",
        "where": "Top Toolbar > Theme Button or Apple Menu > Toggle Dark/Light Theme",
        "steps": [
            "Click the sun/moon icon button on the top toolbar.",
            "Or press Ctrl + T to toggle themes immediately."
        ],
        "shortcut": "Ctrl + T",
        "related": ["preferences", "window-overview"]
    },
    {
        "id": "delete-page",
        "name": "Delete Page",
        "letter": "D",
        "meaning": "Permanently removes the selected page from the active PDF document.",
        "where": "Sidebar Thumbnail Context Menu > Delete Page",
        "steps": [
            "Open the sidebar and locate the target page thumbnail.",
            "Right-click the thumbnail card.",
            "Select Delete Page or press the Delete key."
        ],
        "shortcut": "Delete",
        "related": ["duplicate-page", "insert-blank-page", "organize-pdf-pages"]
    },
    {
        "id": "duplicate-save-as-new-copy",
        "name": "Duplicate / Save As New Copy",
        "letter": "D",
        "meaning": "Saves an independent copy of the document without altering the original.",
        "where": "File > Duplicate / Save As New Copy...",
        "steps": [
            "Select File > Duplicate / Save As New Copy...",
            "Choose a target directory and file name.",
            "Click Save to create the new document copy."
        ],
        "shortcut": "Ctrl + Shift + S",
        "related": ["save", "revert-to-original", "export-dialog"]
    },
    {
        "id": "duplicate-page",
        "name": "Duplicate Page",
        "letter": "D",
        "meaning": "Duplicates the selected page and inserts the clone immediately after.",
        "where": "Sidebar Thumbnail Context Menu > Duplicate Page",
        "steps": [
            "Right-click any page thumbnail card in the sidebar.",
            "Select Duplicate Page from the context menu.",
            "Verify the cloned page appears directly below."
        ],
        "shortcut": "",
        "related": ["delete-page", "insert-blank-page", "organize-pdf-pages"]
    },

    # E
    {
        "id": "ellipse-oval-shape",
        "name": "Oval / Circle Shape",
        "letter": "E",
        "meaning": "Draws vector ellipses and circles with custom stroke and fill colors.",
        "where": "Markup Toolbar > Shapes Dropdown > Oval / Circle",
        "steps": [
            "Click the Shapes dropdown on the Markup Toolbar.",
            "Select Oval / Circle.",
            "Drag on the canvas to draw the shape."
        ],
        "shortcut": "",
        "related": ["rectangle-shape", "shapes-dropdown", "annotate-and-markup"]
    },
    {
        "id": "export-dialog",
        "name": "Export Dialog",
        "letter": "E",
        "meaning": "Exports files to PDF, JPEG, PNG, WebP, or TIFF with resolution options.",
        "where": "File > Export...",
        "steps": [
            "Select File > Export... or press Ctrl + E.",
            "Choose the output format, quality, and DPI resolution.",
            "Click Save to write the converted file to disk."
        ],
        "shortcut": "Ctrl + E",
        "related": ["export-as-pdf", "save-safely", "print"]
    },
    {
        "id": "export-as-pdf",
        "name": "Export as PDF",
        "letter": "E",
        "meaning": "Directly exports current document and annotations as a standard PDF file.",
        "where": "File > Export as PDF...",
        "steps": [
            "Select File > Export as PDF... or press Ctrl + Shift + E.",
            "Specify target destination and file name.",
            "Click Save to generate the PDF."
        ],
        "shortcut": "Ctrl + Shift + E",
        "related": ["export-dialog", "print", "save"]
    },
    {
        "id": "exposure-slider",
        "name": "Exposure Slider",
        "letter": "E",
        "meaning": "Brightens or darkens image highlights and overall light exposure.",
        "where": "Adjust Color Panel > Exposure Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Exposure slider to lighten or darken the picture.",
            "Click Done to confirm the adjustment."
        ],
        "shortcut": "",
        "related": ["adjust-color", "contrast-slider", "auto-levels"]
    },
    {
        "id": "extract-all-text",
        "name": "Extract All Text to File",
        "letter": "E",
        "meaning": "Extracts entire text content across all pages into a plain text file.",
        "where": "Edit > Extract All Text to File...",
        "steps": [
            "Open any PDF document containing readable text.",
            "Select Edit > Extract All Text to File...",
            "Select a target text file name and click Save."
        ],
        "shortcut": "",
        "related": ["copy-text", "search-field"]
    },

    # F
    {
        "id": "fill-color",
        "name": "Fill Color",
        "letter": "F",
        "meaning": "Selects the interior fill color or transparent background for shapes.",
        "where": "Markup Toolbar > Fill Color Dropdown",
        "steps": [
            "Click the Fill Color dropdown on the Markup Toolbar.",
            "Select No Fill (Transparent) or choose a color swatch.",
            "Choose Show Colors... to pick any custom tint."
        ],
        "shortcut": "",
        "related": ["border-stroke-color", "shapes-dropdown", "annotate-and-markup"]
    },
    {
        "id": "first-page-image",
        "name": "First Page / Image",
        "letter": "F",
        "meaning": "Navigates directly to the very first page or image of the document.",
        "where": "Go > First Page / Image",
        "steps": [
            "Select Go > First Page / Image.",
            "Or press the Home key on your keyboard."
        ],
        "shortcut": "Home",
        "related": ["last-page-image", "next-page-image", "previous-page-image"]
    },
    {
        "id": "font-controls",
        "name": "Font Controls",
        "letter": "F",
        "meaning": "Customizes font family, point size, weight, and alignment for text boxes.",
        "where": "Markup Toolbar > Font Size, Font Family, Bold, Italic, Alignment",
        "steps": [
            "Select an existing text annotation on the canvas.",
            "Select a font family and font size from the toolbar controls.",
            "Click Bold, Italic, or Underline to format."
        ],
        "shortcut": "",
        "related": ["text-box-tool", "bold-text", "quick-styles-alignment"]
    },
    {
        "id": "frameless-window-mode",
        "name": "Frameless Window Mode",
        "letter": "F",
        "meaning": "Removes standard window borders for a sleek macOS traffic light title bar.",
        "where": "View > Frameless Window Mode",
        "steps": [
            "Select View > Frameless Window Mode or press F11.",
            "Press F11 again to restore standard window borders."
        ],
        "shortcut": "F11",
        "related": ["traffic-light-buttons", "slideshow-mode"]
    },

    # G
    {
        "id": "go-to-page",
        "name": "Go to Page",
        "letter": "G",
        "meaning": "Opens a number prompt to jump directly to any document page.",
        "where": "Go > Go to Page...",
        "steps": [
            "Select Go > Go to Page... or press Ctrl + G.",
            "Type your target page number.",
            "Press Enter or click OK."
        ],
        "shortcut": "Ctrl + G",
        "related": ["first-page-image", "last-page-image", "view-and-navigate"]
    },

    # H
    {
        "id": "help-window",
        "name": "Help Window",
        "letter": "H",
        "meaning": "Opens the complete Preview documentation system and feature dictionary.",
        "where": "Help > Preview Help",
        "steps": [
            "Select Help > Preview Help or press F1.",
            "Use the left navigation tree or search box to find topics.",
            "Press Esc to close the Help window."
        ],
        "shortcut": "F1",
        "related": ["keyboard-shortcuts-guide", "what-is-preview"]
    },
    {
        "id": "highlighter-tool",
        "name": "Highlighter Tool",
        "letter": "H",
        "meaning": "Draws semi-transparent fluorescent yellow highlights over text and images.",
        "where": "Markup Toolbar > Highlighter Button",
        "steps": [
            "Click the Markup button on the top toolbar.",
            "Click the Highlighter tool button.",
            "Drag over document text or pictures to highlight."
        ],
        "shortcut": "",
        "related": ["pen-tool", "border-stroke-color", "annotate-and-markup"]
    },

    # I
    {
        "id": "insert-blank-page",
        "name": "Insert Blank Page",
        "letter": "I",
        "meaning": "Inserts a new blank white page directly after the current document page.",
        "where": "Edit > Insert Blank Page or Sidebar Thumbnail Context Menu",
        "steps": [
            "Select Edit > Insert Blank Page or press Ctrl + Shift + N.",
            "Or right-click a thumbnail and pick Insert Blank Page After."
        ],
        "shortcut": "Ctrl + Shift + N",
        "related": ["delete-page", "duplicate-page", "organize-pdf-pages"]
    },
    {
        "id": "insert-page-from-file",
        "name": "Insert Page from File",
        "letter": "I",
        "meaning": "Inserts external PDF pages or images into the active document.",
        "where": "Sidebar Thumbnail Context Menu > Insert Page from File...",
        "steps": [
            "Right-click any thumbnail card in the sidebar.",
            "Select Insert Page from File...",
            "Select external PDF or image files to append."
        ],
        "shortcut": "",
        "related": ["insert-blank-page", "merge-pdfs", "organize-pdf-pages"]
    },
    {
        "id": "inspector",
        "name": "Inspector",
        "letter": "I",
        "meaning": "Displays document dimensions, file size, color profile, and PDF metadata.",
        "where": "Tools > Show Inspector or Top Toolbar > Inspector Button",
        "steps": [
            "Click the Inspector button on the top toolbar or press Ctrl + I.",
            "Review General Info for dimensions, DPI, and format.",
            "Click the PDF Details tab for author and keyword metadata."
        ],
        "shortcut": "Ctrl + I",
        "related": ["adjust-size", "window-overview"]
    },
    {
        "id": "italic-text",
        "name": "Italic Text",
        "letter": "I",
        "meaning": "Toggles italic font formatting for active text annotation boxes.",
        "where": "Markup Toolbar > Italic (I) Button",
        "steps": [
            "Select a text annotation on canvas.",
            "Click the I button on the Markup Toolbar.",
            "Or press Ctrl + I while editing text."
        ],
        "shortcut": "Ctrl + I",
        "related": ["bold-text", "underline-text", "text-box-tool"]
    },

    # K
    {
        "id": "keyboard-shortcuts-guide",
        "name": "Keyboard Shortcuts Guide",
        "letter": "K",
        "meaning": "Displays a complete categorized reference table of all application shortcuts.",
        "where": "Help > Keyboard Shortcuts Guide",
        "steps": [
            "Select Help > Keyboard Shortcuts Guide.",
            "Review shortcuts organized by menu category."
        ],
        "shortcut": "",
        "related": ["help-window", "view-and-navigate"]
    },

    # L
    {
        "id": "lasso-selection",
        "name": "Lasso Selection",
        "letter": "L",
        "meaning": "Draws freehand polygonal selection boundaries to crop irregular shapes.",
        "where": "Markup Toolbar > Selection Dropdown > Lasso Selection",
        "steps": [
            "Click the Selection dropdown on the Markup Toolbar.",
            "Select Lasso Selection.",
            "Drag around the irregular area to create a closed selection."
        ],
        "shortcut": "",
        "related": ["rectangular-selection", "oval-selection", "crop-selection"]
    },
    {
        "id": "last-page-image",
        "name": "Last Page / Image",
        "letter": "L",
        "meaning": "Jumps directly to the final page or image in the active document.",
        "where": "Go > Last Page / Image",
        "steps": [
            "Select Go > Last Page / Image.",
            "Or press the End key on your keyboard."
        ],
        "shortcut": "End",
        "related": ["first-page-image", "next-page-image", "previous-page-image"]
    },
    {
        "id": "line-style-thickness",
        "name": "Line Style / Thickness",
        "letter": "L",
        "meaning": "Selects stroke thickness from 1 px fine hairline up to 12 px heavy line.",
        "where": "Markup Toolbar > Line Style / Thickness Dropdown",
        "steps": [
            "Click the Line Style / Thickness dropdown on Markup Toolbar.",
            "Select a thickness: 1 px, 2 px, 3 px, 5 px, 8 px, or 12 px."
        ],
        "shortcut": "",
        "related": ["border-stroke-color", "pen-tool", "shapes-dropdown"]
    },
    {
        "id": "line-tool",
        "name": "Line Tool",
        "letter": "L",
        "meaning": "Draws straight vector line segments on document canvas.",
        "where": "Markup Toolbar > Shapes Dropdown > Line",
        "steps": [
            "Click the Shapes dropdown on the Markup Toolbar.",
            "Select Line.",
            "Drag across canvas from start point to end point."
        ],
        "shortcut": "",
        "related": ["arrow-tool", "shapes-dropdown", "annotate-and-markup"]
    },
    {
        "id": "loupe-magnifier",
        "name": "Loupe / Magnifier",
        "letter": "L",
        "meaning": "Displays a circular magnifying glass following your cursor for close inspection.",
        "where": "Tools > Show Magnifier (Loupe) or press ~ / `",
        "steps": [
            "Press the tilde (~) key or backtick (`) key.",
            "Move your cursor over document details to inspect zoomed pixels.",
            "Press ~ or ` again to dismiss the magnifier."
        ],
        "shortcut": "` / ~ / Ctrl + Shift + M",
        "related": ["zoom-in", "actual-size", "view-and-navigate"]
    },

    # M
    {
        "id": "markup-toolbar",
        "name": "Markup Toolbar",
        "letter": "M",
        "meaning": "Secondary toolbar providing sketch, highlighter, shapes, text, and note tools.",
        "where": "Top Toolbar > Markup Pill Button or Tools > Show Markup Toolbar",
        "steps": [
            "Click the Markup button on the top toolbar or press Ctrl + Shift + A.",
            "Select any annotation tool to draw on canvas.",
            "Click the Markup button again to hide the secondary toolbar."
        ],
        "shortcut": "Ctrl + Shift + A",
        "related": ["annotate-and-markup", "pointer-select-tool", "window-overview"]
    },
    {
        "id": "merge-pdfs",
        "name": "Merge PDFs",
        "letter": "M",
        "meaning": "Combines two or more independent PDF files into a single continuous document.",
        "where": "File > Merge PDFs...",
        "steps": [
            "Select File > Merge PDFs...",
            "Select at least two PDF files to merge.",
            "Choose a target file name and click Save."
        ],
        "shortcut": "",
        "related": ["split-pdf-extract-pages", "organize-pdf-pages", "save-safely"]
    },
    {
        "id": "minimize-window",
        "name": "Minimize Window",
        "letter": "M",
        "meaning": "Minimizes the Preview application window to your system taskbar or dock.",
        "where": "Window > Minimize or Yellow Traffic Light Button",
        "steps": [
            "Select Window > Minimize or press Ctrl + M.",
            "Click the app icon on your system taskbar to restore."
        ],
        "shortcut": "Ctrl + M",
        "related": ["close-window", "frameless-window-mode"]
    },

    # N
    {
        "id": "next-page-image",
        "name": "Next Page / Image",
        "letter": "N",
        "meaning": "Advances view to the next document page or folder image.",
        "where": "Go > Next Page / Image or Top Toolbar > Next Arrow Button",
        "steps": [
            "Click the right arrow button on the top toolbar.",
            "Or press Right Arrow, Down Arrow, or Page Down."
        ],
        "shortcut": "Right Arrow / Down Arrow / Page Down",
        "related": ["previous-page-image", "first-page-image", "last-page-image"]
    },

    # O
    {
        "id": "open-file",
        "name": "Open File",
        "letter": "O",
        "meaning": "Opens a single PDF document or supported image file.",
        "where": "File > Open... or Top Toolbar > Open Button",
        "steps": [
            "Click the Open button on the top toolbar or press Ctrl + O.",
            "Select your file in the file chooser.",
            "Click Open."
        ],
        "shortcut": "Ctrl + O",
        "related": ["open-folder-images", "open-recent", "get-started"]
    },
    {
        "id": "open-folder-images",
        "name": "Open Folder of Images",
        "letter": "O",
        "meaning": "Loads all supported images within a selected directory as a multi-page book.",
        "where": "File > Open Folder... or Top Toolbar > Open Segmented Arrow",
        "steps": [
            "Select File > Open Folder... or press Ctrl + Shift + O.",
            "Choose any folder containing images.",
            "Click Open to browse all images in sequence."
        ],
        "shortcut": "Ctrl + Shift + O",
        "related": ["open-file", "thumbnails-view", "organize-pdf-pages"]
    },
    {
        "id": "open-recent",
        "name": "Open Recent",
        "letter": "O",
        "meaning": "Submenu providing quick access to the 10 most recently opened files.",
        "where": "File > Open Recent",
        "steps": [
            "Select File > Open Recent.",
            "Click any document path to open it immediately."
        ],
        "shortcut": "",
        "related": ["open-file", "clear-recent-menu"]
    },
    {
        "id": "oval-selection",
        "name": "Oval / Elliptical Selection",
        "letter": "O",
        "meaning": "Creates an elliptical selection marquee to crop or rotate circular areas.",
        "where": "Markup Toolbar > Selection Dropdown > Oval / Elliptical Selection",
        "steps": [
            "Click the Selection dropdown on the Markup Toolbar.",
            "Choose Oval / Elliptical Selection.",
            "Drag over canvas to mark the elliptical area."
        ],
        "shortcut": "",
        "related": ["rectangular-selection", "lasso-selection", "crop-selection"]
    },

    # P
    {
        "id": "page-number-pill",
        "name": "Page Number Pill",
        "letter": "P",
        "meaning": "Visual badge showing the active page number and total page count.",
        "where": "Top Toolbar Title Widget & Sidebar Thumbnail Delegate",
        "steps": [
            "Check the badge next to the title or below thumbnail cards.",
            "The active page displays highlighted in accent blue."
        ],
        "shortcut": "",
        "related": ["thumbnails-view", "window-overview"]
    },
    {
        "id": "password-and-encryption",
        "name": "Password and Encryption",
        "letter": "P",
        "meaning": "Protects sensitive PDF files with standard AES-256 password encryption.",
        "where": "File > Set PDF Password / Encryption...",
        "steps": [
            "Open your target PDF document.",
            "Select File > Set PDF Password / Encryption...",
            "Type a secure password and save the file."
        ],
        "shortcut": "",
        "related": ["redaction-tool", "save-safely", "export-as-pdf"]
    },
    {
        "id": "pen-tool",
        "name": "Pen Tool (Sketch)",
        "letter": "P",
        "meaning": "Draws freehand smooth vector sketch strokes on canvas.",
        "where": "Markup Toolbar > Pen Button",
        "steps": [
            "Click the Pen tool button on the Markup Toolbar.",
            "Choose your stroke color and line thickness.",
            "Drag on canvas to draw freehand lines."
        ],
        "shortcut": "",
        "related": ["highlighter-tool", "border-stroke-color", "annotate-and-markup"]
    },
    {
        "id": "pointer-select-tool",
        "name": "Pointer / Select Tool",
        "letter": "P",
        "meaning": "Deactivates active drawing tools and resets cursor to normal selection mode.",
        "where": "Markup Toolbar > Pointer Button",
        "steps": [
            "Click the Pointer button on the Markup Toolbar.",
            "Or press the Esc key on your keyboard."
        ],
        "shortcut": "Esc",
        "related": ["markup-toolbar", "annotate-and-markup"]
    },
    {
        "id": "preferences",
        "name": "Preferences",
        "letter": "P",
        "meaning": "Configures update checks, theme defaults, and startup preferences.",
        "where": "Apple Menu > Preferences...",
        "steps": [
            "Select Preferences... from the Apple Menu or press Ctrl + ,.",
            "Configure your application options."
        ],
        "shortcut": "Ctrl + ,",
        "related": ["dark-light-theme-toggle", "check-for-updates"]
    },
    {
        "id": "previous-page-image",
        "name": "Previous Page / Image",
        "letter": "P",
        "meaning": "Goes back to the preceding document page or folder image.",
        "where": "Go > Previous Page / Image or Top Toolbar > Previous Arrow Button",
        "steps": [
            "Click the left arrow button on the top toolbar.",
            "Or press Left Arrow, Up Arrow, or Page Up."
        ],
        "shortcut": "Left Arrow / Up Arrow / Page Up",
        "related": ["next-page-image", "first-page-image", "last-page-image"]
    },
    {
        "id": "print",
        "name": "Print",
        "letter": "P",
        "meaning": "Sends the active document or image to your system printer.",
        "where": "File > Print...",
        "steps": [
            "Select File > Print... or press Ctrl + P.",
            "Configure target printer, paper size, and copies.",
            "Click Print to send the job."
        ],
        "shortcut": "Ctrl + P",
        "related": ["print-preview", "export-as-pdf"]
    },
    {
        "id": "print-preview",
        "name": "Print Preview",
        "letter": "P",
        "meaning": "Previews exact printer pagination and margins before printing.",
        "where": "File > Print Preview...",
        "steps": [
            "Select File > Print Preview... or press Ctrl + Shift + P.",
            "Inspect margins, orientation, and layout.",
            "Click Print to proceed."
        ],
        "shortcut": "Ctrl + Shift + P",
        "related": ["print", "export-and-print"]
    },

    # Q
    {
        "id": "quick-styles-alignment",
        "name": "Quick Styles / Alignment",
        "letter": "Q",
        "meaning": "Aligns text Left, Center, or Right and selects preset point sizes.",
        "where": "Markup Toolbar > Text Alignment Dropdown (A)",
        "steps": [
            "Select a text annotation on canvas.",
            "Click the Text Alignment dropdown on Markup Toolbar.",
            "Choose Align Left, Align Center, or Align Right."
        ],
        "shortcut": "",
        "related": ["text-box-tool", "font-controls", "bold-text"]
    },
    {
        "id": "quit-document-viewer",
        "name": "Quit Document Viewer",
        "letter": "Q",
        "meaning": "Closes all documents and exits the application cleanly.",
        "where": "Apple Menu > Quit Document Viewer",
        "steps": [
            "Select Apple Menu > Quit Document Viewer or press Ctrl + Q.",
            "Confirm or save changes if prompted."
        ],
        "shortcut": "Ctrl + Q",
        "related": ["close-window", "save-changes-prompt"]
    },

    # R
    {
        "id": "rectangular-selection",
        "name": "Rectangular Selection",
        "letter": "R",
        "meaning": "Draws standard four-corner marquee boxes for cropping and area rotation.",
        "where": "Markup Toolbar > Selection Dropdown > Rectangular Selection",
        "steps": [
            "Click the Selection dropdown on the Markup Toolbar.",
            "Select Rectangular Selection.",
            "Drag across canvas to frame the rectangular region."
        ],
        "shortcut": "",
        "related": ["oval-selection", "lasso-selection", "crop-selection"]
    },
    {
        "id": "rectangle-shape",
        "name": "Rectangle Shape",
        "letter": "R",
        "meaning": "Draws vector rectangular borders and filled boxes on canvas.",
        "where": "Markup Toolbar > Shapes Dropdown > Rectangle",
        "steps": [
            "Click the Shapes dropdown on the Markup Toolbar.",
            "Select Rectangle.",
            "Drag on canvas to place the rectangle."
        ],
        "shortcut": "",
        "related": ["rounded-rectangle-shape", "ellipse-oval-shape", "shapes-dropdown"]
    },
    {
        "id": "redaction-tool",
        "name": "Redaction Tool",
        "letter": "R",
        "meaning": "Marks rectangular blackout bars over confidential text or images.",
        "where": "Markup Toolbar > Redact Button",
        "steps": [
            "Click the Redaction tool on the Markup Toolbar.",
            "Drag over private text or sensitive numbers.",
            "Select Edit > Apply All Redactions to permanently sanitize."
        ],
        "shortcut": "",
        "related": ["apply-all-redactions", "password-and-encryption", "save-safely"]
    },
    {
        "id": "redo",
        "name": "Redo",
        "letter": "R",
        "meaning": "Re-applies the most recently undone annotation or editing action.",
        "where": "Edit > Redo",
        "steps": [
            "Select Edit > Redo.",
            "Or press Ctrl + Shift + Z."
        ],
        "shortcut": "Ctrl + Shift + Z",
        "related": ["undo", "save-safely"]
    },
    {
        "id": "revert-to-original",
        "name": "Revert to Original",
        "letter": "R",
        "meaning": "Discards all session modifications and reloads the file from disk.",
        "where": "File > Revert to Original...",
        "steps": [
            "Select File > Revert to Original...",
            "Confirm the reload prompt.",
            "The document resets to its pristine disk state."
        ],
        "shortcut": "",
        "related": ["save", "duplicate-save-as-new-copy", "save-safely"]
    },
    {
        "id": "rotate-left",
        "name": "Rotate Left",
        "letter": "R",
        "meaning": "Rotates current document page or image 90 degrees counter-clockwise.",
        "where": "Tools > Rotate Left or Markup Toolbar > Rotate Left Button",
        "steps": [
            "Select Tools > Rotate Left.",
            "Or press Ctrl + L."
        ],
        "shortcut": "Ctrl + L",
        "related": ["rotate-right", "rotate-selection", "select-crop-and-rotate"]
    },
    {
        "id": "rotate-right",
        "name": "Rotate Right",
        "letter": "R",
        "meaning": "Rotates current document page or image 90 degrees clockwise.",
        "where": "Tools > Rotate Right or Top Toolbar > Rotate Button",
        "steps": [
            "Click the Rotate button on the top toolbar.",
            "Or press Ctrl + R."
        ],
        "shortcut": "Ctrl + R",
        "related": ["rotate-left", "rotate-selection", "select-crop-and-rotate"]
    },
    {
        "id": "rotate-selection",
        "name": "Rotate Selection",
        "letter": "R",
        "meaning": "Rotates only the active selected area or annotation 90 degrees clockwise.",
        "where": "Markup Toolbar > Rotate Selection Button or Canvas Selection Menu",
        "steps": [
            "Create a rectangular, oval, or lasso selection.",
            "Click the Rotate Selection button on the Markup Toolbar.",
            "Or right-click the selection and choose Rotate Selection 90°."
        ],
        "shortcut": "Ctrl + R (with selection)",
        "related": ["rotate-right", "crop-selection", "rectangular-selection"]
    },
    {
        "id": "rounded-rectangle-shape",
        "name": "Rounded Rectangle Shape",
        "letter": "R",
        "meaning": "Draws vector rectangles with smooth rounded corner fillets.",
        "where": "Markup Toolbar > Shapes Dropdown > Rounded Rectangle",
        "steps": [
            "Click the Shapes dropdown on the Markup Toolbar.",
            "Select Rounded Rectangle.",
            "Drag on canvas to place the rounded box."
        ],
        "shortcut": "",
        "related": ["rectangle-shape", "shapes-dropdown", "annotate-and-markup"]
    },

    # S
    {
        "id": "saturation-slider",
        "name": "Saturation Slider",
        "letter": "S",
        "meaning": "Adjusts intensity of image color vividness from grayscale to rich color.",
        "where": "Adjust Color Panel > Saturation Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Saturation slider to increase or decrease color vibrancy.",
            "Click Done to apply."
        ],
        "shortcut": "",
        "related": ["adjust-color", "sepia-tone", "exposure-slider"]
    },
    {
        "id": "save",
        "name": "Save",
        "letter": "S",
        "meaning": "Saves all current annotations, rotations, and edits directly into the file.",
        "where": "File > Save",
        "steps": [
            "Select File > Save.",
            "Or press Ctrl + S."
        ],
        "shortcut": "Ctrl + S",
        "related": ["duplicate-save-as-new-copy", "revert-to-original", "save-safely"]
    },
    {
        "id": "save-changes-prompt",
        "name": "Save Changes Prompt",
        "letter": "S",
        "meaning": "Alert sheet protecting against accidental data loss when closing edited files.",
        "where": "Displayed automatically when closing documents with unsaved changes",
        "steps": [
            "Press Enter or click Save to save modifications.",
            "Press Alt + D or click Don't Save to discard changes.",
            "Press Esc or click Cancel to stay in the document."
        ],
        "shortcut": "Enter (Save) / Alt + D (Don't Save) / Esc (Cancel)",
        "related": ["save", "close-window", "save-safely"]
    },
    {
        "id": "scale-proportionally",
        "name": "Scale Proportionally",
        "letter": "S",
        "meaning": "Locks the aspect ratio so image proportions do not distort when resizing.",
        "where": "Adjust Size Dialog > Scale proportionally Checkbox",
        "steps": [
            "Select Tools > Adjust Size... or press Ctrl + Alt + S.",
            "Ensure Scale proportionally remains checked.",
            "Enter a new width, and the height calculates automatically."
        ],
        "shortcut": "",
        "related": ["adjust-size", "resample-image", "inspector"]
    },
    {
        "id": "search-field",
        "name": "Search Field",
        "letter": "S",
        "meaning": "Searches text across document pages with immediate highlight feedback.",
        "where": "Top Toolbar > Search Input Box",
        "steps": [
            "Click the Search input box on the top toolbar.",
            "Type your query keyword and press Enter.",
            "Matches highlight across pages on the canvas."
        ],
        "shortcut": "Ctrl + F",
        "related": ["copy-text", "view-and-navigate"]
    },
    {
        "id": "sepia-tone",
        "name": "Sepia Tone",
        "letter": "S",
        "meaning": "Applies warm brownish antique monochrome toning to photographic imagery.",
        "where": "Adjust Color Panel > Sepia Tone Checkbox",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Check the Sepia Tone checkbox.",
            "Click Done to apply the vintage coloring."
        ],
        "shortcut": "",
        "related": ["adjust-color", "saturation-slider", "auto-levels"]
    },
    {
        "id": "sharpness-slider",
        "name": "Sharpness Slider",
        "letter": "S",
        "meaning": "Sharpens edge clarity or softens harsh textures in photographic images.",
        "where": "Adjust Color Panel > Sharpness Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Sharpness slider to enhance edge definition.",
            "Click Done to save the filtered image."
        ],
        "shortcut": "",
        "related": ["adjust-color", "contrast-slider", "exposure-slider"]
    },
    {
        "id": "sidebar",
        "name": "Sidebar",
        "letter": "S",
        "meaning": "Collapsible left panel displaying Thumbnails, Contact Sheet, or Outline.",
        "where": "Top Toolbar > Sidebar Button or View > Toggle Sidebar",
        "steps": [
            "Click the Sidebar button on the top toolbar.",
            "Or press Ctrl + B to toggle visibility."
        ],
        "shortcut": "Ctrl + B",
        "related": ["thumbnails-view", "contact-sheet-view", "table-of-contents-view"]
    },
    {
        "id": "sidebar-size-slider",
        "name": "Sidebar Size Slider",
        "letter": "S",
        "meaning": "Adjusts the width and height of page thumbnail cards in the sidebar.",
        "where": "Sidebar Footer > Slider",
        "steps": [
            "Open the left sidebar.",
            "Drag the horizontal slider in the sidebar footer.",
            "Thumbnails expand from 70 px up to 220 px."
        ],
        "shortcut": "",
        "related": ["sidebar", "thumbnails-view"]
    },
    {
        "id": "signature-tool",
        "name": "Signature Tool",
        "letter": "S",
        "meaning": "Draws and places transparent vector signatures on contracts and documents.",
        "where": "Markup Toolbar > Signatures Button",
        "steps": [
            "Click the Signatures button on the Markup Toolbar.",
            "Draw your signature with mouse or trackpad on the pad.",
            "Click Insert Signature to place it onto the page."
        ],
        "shortcut": "",
        "related": ["annotate-and-markup", "redaction-tool", "save-safely"]
    },
    {
        "id": "single-page-view",
        "name": "Single Page View",
        "letter": "S",
        "meaning": "Displays one page at a time centered cleanly in the canvas viewport.",
        "where": "View > PDF View Mode > Single Page",
        "steps": [
            "Select View > PDF View Mode > Single Page.",
            "Navigate pages sequentially using arrow keys."
        ],
        "shortcut": "",
        "related": ["two-pages-continuous-view", "slideshow-mode", "view-and-navigate"]
    },
    {
        "id": "slideshow-mode",
        "name": "Slideshow Mode",
        "letter": "S",
        "meaning": "Presents document pages in a distraction-free full-screen presentation mode.",
        "where": "View > Slideshow Mode",
        "steps": [
            "Select View > Slideshow Mode or press F5.",
            "Use arrow keys to advance slides.",
            "Press Esc to exit presentation mode."
        ],
        "shortcut": "F5",
        "related": ["frameless-window-mode", "view-and-navigate"]
    },
    {
        "id": "split-pdf-extract-pages",
        "name": "Split PDF / Extract Pages",
        "letter": "S",
        "meaning": "Extracts specified page numbers or ranges into a separate new PDF document.",
        "where": "File > Split PDF / Extract Pages...",
        "steps": [
            "Open a multi-page PDF document.",
            "Select File > Split PDF / Extract Pages...",
            "Enter page numbers or ranges like 1-3, 5 and click OK."
        ],
        "shortcut": "",
        "related": ["merge-pdfs", "organize-pdf-pages", "export-as-pdf"]
    },
    {
        "id": "sticky-note-tool",
        "name": "Sticky Note Tool",
        "letter": "S",
        "meaning": "Places yellow popover Post-it note annotations for comments and reminders.",
        "where": "Markup Toolbar > Note Button",
        "steps": [
            "Click the Note button on the Markup Toolbar.",
            "Click on the document page where you want the note.",
            "Type your comments and click Done."
        ],
        "shortcut": "",
        "related": ["text-box-tool", "annotate-and-markup"]
    },
    {
        "id": "strikethrough-selected-text",
        "name": "Strikethrough Selected Text",
        "letter": "S",
        "meaning": "Draws a horizontal cancellation strike line across highlighted text.",
        "where": "Canvas Context Menu (with text selected) > Strikethrough Selected Text",
        "steps": [
            "Drag over text to select words on the canvas.",
            "Right-click the selection.",
            "Choose Strikethrough Selected Text."
        ],
        "shortcut": "",
        "related": ["highlighter-tool", "copy-text", "redaction-tool"]
    },

    # T
    {
        "id": "table-of-contents-view",
        "name": "Table of Contents View",
        "letter": "T",
        "meaning": "Displays the hierarchical PDF document outline and chapter bookmarks.",
        "where": "Sidebar Header Dropdown > Table of Contents",
        "steps": [
            "Click the Sidebar button on the top toolbar.",
            "Select Table of Contents from the header view dropdown.",
            "Click any chapter title in the tree to jump to that page."
        ],
        "shortcut": "",
        "related": ["thumbnails-view", "sidebar", "view-and-navigate"]
    },
    {
        "id": "temperature-slider",
        "name": "Temperature Slider",
        "letter": "T",
        "meaning": "Adjusts white balance warmth from cool blue to warm amber hues.",
        "where": "Adjust Color Panel > Temperature Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Temperature slider left for cooler tones or right for warmer tones.",
            "Click Done to confirm."
        ],
        "shortcut": "",
        "related": ["adjust-color", "tint-slider", "auto-levels"]
    },
    {
        "id": "text-box-tool",
        "name": "Text Box Tool",
        "letter": "T",
        "meaning": "Inserts editable vector typography annotation boxes on document pages.",
        "where": "Markup Toolbar > Text Button",
        "steps": [
            "Click the Text tool button on the Markup Toolbar.",
            "Click on canvas to place the text box.",
            "Type your message and format using toolbar font controls."
        ],
        "shortcut": "",
        "related": ["font-controls", "sticky-note-tool", "annotate-and-markup"]
    },
    {
        "id": "theme-toggle",
        "name": "Theme Toggle",
        "letter": "T",
        "meaning": "Toggles application appearance between macOS Dark Mode and Light Mode.",
        "where": "Top Toolbar > Theme Button or Apple Menu > Toggle Dark/Light Theme",
        "steps": [
            "Click the sun/moon button on the top toolbar.",
            "Or press Ctrl + T."
        ],
        "shortcut": "Ctrl + T",
        "related": ["dark-light-theme-toggle", "window-overview"]
    },
    {
        "id": "thumbnails-view",
        "name": "Thumbnails View",
        "letter": "T",
        "meaning": "Displays a vertical list of page cards with page number pill badges.",
        "where": "Sidebar Header Dropdown > Thumbnails",
        "steps": [
            "Click the Sidebar button on the top toolbar or press Ctrl + B.",
            "Select Thumbnails from the sidebar view menu.",
            "Click any page card to jump to it, or drag cards to reorder pages."
        ],
        "shortcut": "",
        "related": ["contact-sheet-view", "table-of-contents-view", "organize-pdf-pages"]
    },
    {
        "id": "tint-slider",
        "name": "Tint Slider",
        "letter": "T",
        "meaning": "Adjusts green and magenta color cast balance in photographic images.",
        "where": "Adjust Color Panel > Tint Slider",
        "steps": [
            "Select Tools > Adjust Color... or press Ctrl + Alt + C.",
            "Drag the Tint slider left for green correction or right for magenta.",
            "Click Done to confirm."
        ],
        "shortcut": "",
        "related": ["adjust-color", "temperature-slider", "auto-levels"]
    },
    {
        "id": "toggle-status-bar",
        "name": "Toggle Status Bar",
        "letter": "T",
        "meaning": "Shows or hides the bottom status information bar displaying document hints.",
        "where": "View > Toggle Status Bar",
        "steps": [
            "Select View > Toggle Status Bar.",
            "The bottom status line toggles visible or hidden."
        ],
        "shortcut": "",
        "related": ["window-overview", "view-and-navigate"]
    },
    {
        "id": "traffic-light-buttons",
        "name": "Traffic Light Buttons",
        "letter": "T",
        "meaning": "macOS-authentic Close (red), Minimize (yellow), and Zoom (green) buttons.",
        "where": "Top Left of Toolbar in Frameless Mode",
        "steps": [
            "Click Red to close window with unsaved verification.",
            "Click Yellow to minimize to taskbar.",
            "Click Green to maximize or restore window."
        ],
        "shortcut": "",
        "related": ["frameless-window-mode", "close-window", "minimize-window"]
    },
    {
        "id": "two-pages-continuous-view",
        "name": "Two Pages Continuous (Two-Up) View",
        "letter": "T",
        "meaning": "Displays facing page spreads side by side in a book-style reading layout.",
        "where": "View > PDF View Mode > Two Pages Continuous (Two-Up)",
        "steps": [
            "Select View > PDF View Mode > Two Pages Continuous (Two-Up).",
            "Scroll through pages as facing book spreads."
        ],
        "shortcut": "",
        "related": ["single-page-view", "view-and-navigate"]
    },

    # U
    {
        "id": "underline-text",
        "name": "Underline Text",
        "letter": "U",
        "meaning": "Toggles underline text decoration on active text annotation boxes.",
        "where": "Markup Toolbar > Underline (U) Button",
        "steps": [
            "Select a text annotation on canvas.",
            "Click the U button on the Markup Toolbar.",
            "Or press Ctrl + U while typing."
        ],
        "shortcut": "Ctrl + U",
        "related": ["bold-text", "italic-text", "text-box-tool"]
    },
    {
        "id": "undo",
        "name": "Undo",
        "letter": "U",
        "meaning": "Reverts the previous drawing stroke, annotation, crop, or deletion.",
        "where": "Edit > Undo",
        "steps": [
            "Select Edit > Undo.",
            "Or press Ctrl + Z."
        ],
        "shortcut": "Ctrl + Z",
        "related": ["redo", "save-safely"]
    },
    {
        "id": "update-banner",
        "name": "Update Banner",
        "letter": "U",
        "meaning": "Non-intrusive notification bar appearing when a new release is detected.",
        "where": "Top of window below toolbar when update is available",
        "steps": [
            "Click View Update to open the download sheet.",
            "Or click the X button to dismiss the banner."
        ],
        "shortcut": "",
        "related": ["check-for-updates", "about-document-viewer"]
    },

    # Z
    {
        "id": "zoom-in",
        "name": "Zoom In",
        "letter": "Z",
        "meaning": "Increases canvas magnification scale by 20 percent.",
        "where": "View > Zoom In or Top Toolbar > Zoom In (+) Button",
        "steps": [
            "Click the plus (+) button on the top toolbar.",
            "Or press Ctrl + = (or Ctrl + +).",
            "Or hold Ctrl and scroll mouse wheel up."
        ],
        "shortcut": "Ctrl + =",
        "related": ["zoom-out", "zoom-to-fit", "actual-size"]
    },
    {
        "id": "zoom-out",
        "name": "Zoom Out",
        "letter": "Z",
        "meaning": "Decreases canvas magnification scale by 20 percent.",
        "where": "View > Zoom Out or Top Toolbar > Zoom Out (-) Button",
        "steps": [
            "Click the minus (-) button on the top toolbar.",
            "Or press Ctrl + -.",
            "Or hold Ctrl and scroll mouse wheel down."
        ],
        "shortcut": "Ctrl + -",
        "related": ["zoom-in", "zoom-to-fit", "actual-size"]
    },
    {
        "id": "zoom-to-fit",
        "name": "Zoom to Fit",
        "letter": "Z",
        "meaning": "Scales document page to fit completely within the window viewport.",
        "where": "View > Zoom to Fit or Canvas Context Menu > Zoom to Fit",
        "steps": [
            "Select View > Zoom to Fit.",
            "Or press Ctrl + 9."
        ],
        "shortcut": "Ctrl + 9",
        "related": ["zoom-to-width", "actual-size", "zoom-in"]
    },
    {
        "id": "zoom-to-width",
        "name": "Zoom to Width",
        "letter": "Z",
        "meaning": "Scales document page width to fill window width while allowing vertical scroll.",
        "where": "View > Zoom to Width",
        "steps": [
            "Select View > Zoom to Width.",
            "Page width automatically expands to match canvas viewport width."
        ],
        "shortcut": "",
        "related": ["zoom-to-fit", "actual-size", "view-and-navigate"]
    }
]

# Sort alphabetically by name
entries.sort(key=lambda e: e["name"].lower())

out_file = "help/content/dictionary.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({"total": len(entries), "entries": entries}, f, indent=2)

print(f"Generated {len(entries)} dictionary entries in {out_file}")
