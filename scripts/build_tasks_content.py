#!/usr/bin/env python3
"""Generates task content files for Preview Help."""

import json
import os

tasks = [
    {
        "id": "view-and-navigate",
        "title": "View and navigate documents",
        "summary": "Navigate pages, adjust zoom levels, and search text within documents.",
        "sections": [
            {
                "heading": "Scrolling and Panning",
                "text": "Scroll using your mouse wheel or trackpad. Hold the Spacebar and drag with the mouse to pan the document."
            },
            {
                "heading": "Zoom Controls",
                "text": "Click the minus and plus buttons on the toolbar to zoom. Select View > Actual Size or View > Zoom to Fit."
            },
            {
                "heading": "Searching Text",
                "text": "Click the Search box on the toolbar or press Ctrl + F. Type your search term and press Enter."
            }
        ],
        "steps": [
            "Press the Right Arrow key or Left Arrow key to move between pages.",
            "Select Go > Go to Page... or press Ctrl + G to jump directly to a page number.",
            "Press Ctrl + 9 to fit the page to the window, or press Ctrl + 0 for actual size."
        ],
        "note": "Press the tilde (~) key or backtick (`) to toggle the circular magnifier loupe.",
        "related": [
            "use-the-sidebar",
            "organize-pdf-pages",
            "window-overview"
        ]
    },
    {
        "id": "use-the-sidebar",
        "title": "Use the sidebar",
        "summary": "Browse document pages with thumbnails or jump through chapters using the Table of Contents.",
        "sections": [
            {
                "heading": "Sidebar Views",
                "text": "Click the sidebar header menu to choose Thumbnails, Contact Sheet, or Table of Contents."
            },
            {
                "heading": "Thumbnail Resizing",
                "text": "Drag the slider at the bottom of the sidebar to increase or decrease thumbnail preview size."
            }
        ],
        "steps": [
            "Click the Sidebar button on the top toolbar or press Ctrl + B to open the sidebar.",
            "Select Thumbnails to view a vertical strip of all pages.",
            "Select Table of Contents to navigate PDF chapters and outline bookmarks."
        ],
        "note": "Right-click any thumbnail card to access quick page rotation, duplicate, insert, and delete commands.",
        "related": [
            "view-and-navigate",
            "organize-pdf-pages",
            "window-overview"
        ]
    },
    {
        "id": "annotate-and-markup",
        "title": "Annotate and mark up",
        "summary": "Draw freehand sketch lines, highlight text, create shapes, add text boxes, and insert sticky notes.",
        "sections": [
            {
                "heading": "Markup Toolbar",
                "text": "Click the Markup button on the top toolbar to display the secondary annotation bar."
            },
            {
                "heading": "Color and Line Controls",
                "text": "Use the stroke color, fill color, and line thickness menus to style your annotations."
            }
        ],
        "steps": [
            "Click the Markup button on the toolbar or press Ctrl + Shift + A.",
            "Select the Pen or Highlighter tool and drag on the canvas to draw.",
            "Click the Shapes dropdown to add rectangles, circles, lines, or arrows.",
            "Click the Text tool to type annotation boxes, or click Note to add a yellow sticky note."
        ],
        "note": "Press the Esc key or click the Pointer button on the Markup Toolbar to return to select mode.",
        "related": [
            "select-crop-and-rotate",
            "sign-documents",
            "redact-content"
        ]
    },
    {
        "id": "select-crop-and-rotate",
        "title": "Select, crop and rotate",
        "summary": "Make rectangular, oval, or lasso selections to crop pictures or rotate selected areas.",
        "sections": [
            {
                "heading": "Selection Modes",
                "text": "Choose Rectangular Selection, Oval Selection, or Lasso Selection from the selection dropdown menu."
            },
            {
                "heading": "Cropping and Rotation",
                "text": "Crop selection cuts away the outer area. Rotate selection turns only the selected pixel box."
            }
        ],
        "steps": [
            "Click the Selection dropdown on the Markup Toolbar and choose a selection tool.",
            "Drag over the document canvas to mark the desired boundary.",
            "Click the Crop button or press Ctrl + K to crop the document to your selection.",
            "Click the Rotate Selection button or press Ctrl + R to rotate the selection 90 degrees."
        ],
        "note": "To rotate the entire page instead of a selection, use Tools > Rotate Left or Tools > Rotate Right.",
        "related": [
            "annotate-and-markup",
            "adjust-size",
            "save-safely"
        ]
    },
    {
        "id": "sign-documents",
        "title": "Sign documents",
        "summary": "Draw and store your handwritten signature to sign digital contracts and PDF documents.",
        "sections": [
            {
                "heading": "Signature Pad",
                "text": "The signature window provides a smooth drawing pad with baseline guides for trackpads and mice."
            }
        ],
        "steps": [
            "Click the Markup button on the top toolbar to display markup tools.",
            "Click the Signatures button on the Markup Toolbar.",
            "Draw your handwritten signature on the canvas pad using your mouse or trackpad.",
            "Click Insert Signature to place the transparent vector signature onto the document page."
        ],
        "note": "Drag the placed signature to reposition it, or drag its corner handles to resize.",
        "related": [
            "annotate-and-markup",
            "redact-content",
            "save-safely"
        ]
    },
    {
        "id": "redact-content",
        "title": "Redact content",
        "summary": "Permanently black out confidential text and sensitive imagery before sharing documents.",
        "sections": [
            {
                "heading": "Redaction Marking",
                "text": "Draw black redaction boxes over sensitive numbers, names, or addresses on any document page."
            },
            {
                "heading": "Permanent Application",
                "text": "Applying redactions strips the underlying text bytes and pixels completely from the PDF structure."
            }
        ],
        "steps": [
            "Click the Redaction tool on the Markup Toolbar.",
            "Drag black boxes over the private text or images you wish to hide.",
            "Select Edit > Apply All Redactions.",
            "Click Yes on the confirmation alert to permanently erase the covered content."
        ],
        "note": "Permanent redaction cannot be undone after saving. Keep a backup copy of your original file.",
        "related": [
            "annotate-and-markup",
            "password-and-encryption",
            "save-safely"
        ]
    },
    {
        "id": "adjust-color",
        "title": "Adjust color",
        "summary": "Tune image exposure, contrast, saturation, temperature, tint, and sharpness with live histogram feedback.",
        "sections": [
            {
                "heading": "Color Sliders",
                "text": "Adjust sliders smoothly with immediate real-time canvas updates. The RGB histogram reflects tone distribution."
            }
        ],
        "steps": [
            "Select Tools > Adjust Color... or click the Adjust Color button on the Markup Toolbar.",
            "Click Auto Levels for automatic tonal correction, or drag individual sliders.",
            "Check Sepia Tone for a vintage warm monochromatic effect if desired.",
            "Click Done to apply the color adjustments, or click Revert to restore original colors."
        ],
        "note": "Adjust Color is designed for images and photos, not text-only PDF pages.",
        "related": [
            "adjust-size",
            "select-crop-and-rotate",
            "save-safely"
        ]
    },
    {
        "id": "adjust-size",
        "title": "Adjust size",
        "summary": "Resize image dimensions and change print resolution with proportional aspect ratio lock.",
        "sections": [
            {
                "heading": "Dimension Presets",
                "text": "Pick common display dimensions such as 1920x1080 Full HD or enter custom pixel values."
            }
        ],
        "steps": [
            "Select Tools > Adjust Size... or click the Adjust Size button on the Markup Toolbar.",
            "Keep Scale proportionally checked to maintain original image proportions.",
            "Enter your target Width or Height in pixels or percent.",
            "Set the print resolution in pixels per inch, then click OK."
        ],
        "note": "Check the resulting size label at the bottom of the window to preview file weight.",
        "related": [
            "adjust-color",
            "select-crop-and-rotate",
            "export-and-print"
        ]
    },
    {
        "id": "organize-pdf-pages",
        "title": "Organize PDF pages",
        "summary": "Reorder, delete, duplicate, and insert pages in multi-page PDF documents.",
        "sections": [
            {
                "heading": "Thumbnails Drag and Drop",
                "text": "Drag thumbnail cards up or down in the sidebar to reorganize page sequence immediately."
            }
        ],
        "steps": [
            "Select View > Toggle Sidebar or press Ctrl + B to open the left sidebar.",
            "Drag a page thumbnail to a new location in the list to reorder it.",
            "Right-click any thumbnail and select Duplicate Page to copy the active page.",
            "Right-click a thumbnail and select Delete Page to remove that page from the document."
        ],
        "note": "Select Edit > Insert Blank Page or press Ctrl + Shift + N to insert a fresh white page.",
        "related": [
            "use-the-sidebar",
            "merge-and-split-pdfs",
            "save-safely"
        ]
    },
    {
        "id": "save-safely",
        "title": "Save safely",
        "summary": "Save updates directly, export duplicate copies, revert changes, and prevent accidental data loss.",
        "sections": [
            {
                "heading": "Saving Modifications",
                "text": "Saving writes your annotations and edits into the document. Save As creates an independent duplicate."
            },
            {
                "heading": "Unsaved Edits Confirmation",
                "text": "Closing the window with unsaved edits displays a prompt offering Don't Save, Cancel, or Save."
            }
        ],
        "steps": [
            "Select File > Save or press Ctrl + S to update the current file.",
            "Select File > Duplicate / Save As New Copy... or press Ctrl + Shift + S for a new file.",
            "Select File > Revert to Original... to discard all session modifications and reload the file."
        ],
        "note": "The prompt lets you press Alt + D to discard changes or Enter to save safely.",
        "related": [
            "export-and-print",
            "organize-pdf-pages",
            "what-is-preview"
        ]
    },
    {
        "id": "export-and-print",
        "title": "Export and print",
        "summary": "Export documents to PDF, PNG, JPEG, WebP, or TIFF, and send pages to system printers.",
        "sections": [
            {
                "heading": "Export Sheet",
                "text": "Configure output format, compression quality, resolution DPI, and page scope in the export window."
            }
        ],
        "steps": [
            "Select File > Export... or press Ctrl + E to open the Export dialog.",
            "Select your desired Format: PDF, JPEG, PNG, WebP, or TIFF.",
            "Choose your target resolution from 72 DPI screen up to 600 DPI ultra print.",
            "Click Save to export your file.",
            "To print directly, select File > Print... or press Ctrl + P."
        ],
        "note": "Select File > Print Preview... or press Ctrl + Shift + P to review page layouts before printing.",
        "related": [
            "save-safely",
            "adjust-size",
            "password-and-encryption"
        ]
    },
    {
        "id": "merge-and-split-pdfs",
        "title": "Merge and split PDFs",
        "summary": "Combine multiple PDF documents together or extract specific page ranges into new files.",
        "sections": [
            {
                "heading": "Merging PDFs",
                "text": "Select two or more PDF files. Preview merges them in order into a single unified file."
            },
            {
                "heading": "Splitting Pages",
                "text": "Extract individual pages or ranges like 1-3, 5 into a brand new document."
            }
        ],
        "steps": [
            "To combine files, select File > Merge PDFs... and pick at least two PDF documents.",
            "Save the resulting combined PDF to your desired disk location.",
            "To extract pages, open your document and select File > Split PDF / Extract Pages...",
            "Enter page numbers or ranges like 1-4, 7 and click OK to save the extracted PDF."
        ],
        "note": "You can also insert individual pages from external files by right-clicking a thumbnail card.",
        "related": [
            "organize-pdf-pages",
            "export-and-print",
            "password-and-encryption"
        ]
    },
    {
        "id": "password-and-encryption",
        "title": "Password and encryption",
        "summary": "Protect confidential PDF documents with AES-256 standard encryption and password security.",
        "sections": [
            {
                "heading": "AES-256 PDF Encryption",
                "text": "Setting a document password locks the file so readers must provide the password to open it."
            }
        ],
        "steps": [
            "Open the PDF document you wish to protect.",
            "Select File > Set PDF Password / Encryption...",
            "Enter your secure password in the input prompt and click OK.",
            "Select File > Save to write the encrypted PDF to disk."
        ],
        "note": "Keep your password safe. Encrypted documents cannot be recovered if the password is lost.",
        "related": [
            "redact-content",
            "save-safely",
            "export-and-print"
        ]
    }
]

out_dir = "help/content/tasks"
os.makedirs(out_dir, exist_ok=True)
for task in tasks:
    filename = os.path.join(out_dir, f"{task['id'].replace('-', '_')}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(task, f, indent=2)
    print(f"Wrote {filename}")
print(f"Successfully generated all {len(tasks)} task files.")
