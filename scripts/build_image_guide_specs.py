#!/usr/bin/env python3
"""Builds annotation specifications for the 13 task screenshots in Image Guide."""

import json
import os

specs = [
    # 1. view-and-navigate
    {
        "id": "view-and-navigate",
        "task_id": "view-and-navigate",
        "title": "View and navigate documents",
        "source_image": "help/screenshots_clean/guide-toolbar-overview-light.png",
        "output_image": "guide-view-and-navigate-1.png",
        "caption": "Toolbar navigation buttons and zoom controls in Preview.",
        "alt_text": "Preview navigation toolbar showing previous, next, and zoom buttons",
        "annotations": [
            {"type": "box", "x": 68, "y": 8, "w": 62, "h": 32},
            {"type": "arrow", "x1": 50, "y1": 55, "x2": 82, "y2": 38},
            {"type": "number", "x": 42, "y": 62, "text": "1"},
            {"type": "box", "x": 580, "y": 8, "w": 62, "h": 32},
            {"type": "arrow", "x1": 605, "y1": 65, "x2": 605, "y2": 42},
            {"type": "number", "x": 605, "y": 78, "text": "2"},
            {"type": "box", "x": 688, "y": 8, "w": 140, "h": 32},
            {"type": "arrow", "x1": 740, "y1": 65, "x2": 740, "y2": 42},
            {"type": "number", "x": 740, "y": 78, "text": "3"}
        ]
    },
    # 2. use-the-sidebar
    {
        "id": "use-the-sidebar",
        "task_id": "use-the-sidebar",
        "title": "Use the sidebar",
        "source_image": "help/screenshots_clean/guide-sidebar-thumbnails-light.png",
        "output_image": "guide-use-the-sidebar-1.png",
        "caption": "Sidebar view dropdown and page thumbnail cards.",
        "alt_text": "Left sidebar displaying page thumbnail cards and size slider",
        "annotations": [
            {"type": "box", "x": 10, "y": 6, "w": 115, "h": 28},
            {"type": "arrow", "x1": 150, "y1": 20, "x2": 128, "y2": 20},
            {"type": "number", "x": 165, "y": 20, "text": "1"},
            {"type": "box", "x": 12, "y": 48, "w": 140, "h": 160},
            {"type": "arrow", "x1": 175, "y1": 120, "x2": 155, "y2": 120},
            {"type": "number", "x": 190, "y": 120, "text": "2"},
            {"type": "box", "x": 10, "y": 486, "w": 148, "h": 24},
            {"type": "arrow", "x1": 180, "y1": 498, "x2": 160, "y2": 498},
            {"type": "number", "x": 195, "y": 498, "text": "3"}
        ]
    },
    # 3. annotate-and-markup
    {
        "id": "annotate-and-markup",
        "task_id": "annotate-and-markup",
        "title": "Annotate and mark up",
        "source_image": "help/screenshots_clean/guide-markup-tools-light.png",
        "output_image": "guide-annotate-and-markup-1.png",
        "caption": "Markup Toolbar with sketch, shapes, text, and note tools.",
        "alt_text": "Secondary Markup Toolbar with annotation drawing and shape controls",
        "annotations": [
            {"type": "box", "x": 48, "y": 4, "w": 38, "h": 30},
            {"type": "arrow", "x1": 66, "y1": 55, "x2": 66, "y2": 36},
            {"type": "number", "x": 66, "y": 68, "text": "1"},
            {"type": "box", "x": 90, "y": 4, "w": 72, "h": 30},
            {"type": "arrow", "x1": 126, "y1": 55, "x2": 126, "y2": 36},
            {"type": "number", "x": 126, "y": 68, "text": "2"},
            {"type": "box", "x": 166, "y": 4, "w": 104, "h": 30},
            {"type": "arrow", "x1": 218, "y1": 55, "x2": 218, "y2": 36},
            {"type": "number", "x": 218, "y": 68, "text": "3"}
        ]
    },
    # 4. select-crop-and-rotate
    {
        "id": "select-crop-and-rotate",
        "task_id": "select-crop-and-rotate",
        "title": "Select, crop and rotate",
        "source_image": "help/screenshots_clean/guide-markup-tools-light.png",
        "output_image": "guide-select-crop-and-rotate-1.png",
        "caption": "Selection dropdown, crop button, and rotate selection action.",
        "alt_text": "Selection marquee tool and crop button on the Markup Toolbar",
        "annotations": [
            {"type": "box", "x": 46, "y": 4, "w": 40, "h": 30},
            {"type": "arrow", "x1": 66, "y1": 55, "x2": 66, "y2": 36},
            {"type": "number", "x": 66, "y": 68, "text": "1"},
            {"type": "box", "x": 780, "y": 4, "w": 32, "h": 30},
            {"type": "arrow", "x1": 796, "y1": 55, "x2": 796, "y2": 36},
            {"type": "number", "x": 796, "y": 68, "text": "2"},
            {"type": "box", "x": 816, "y": 4, "w": 32, "h": 30},
            {"type": "arrow", "x1": 832, "y1": 55, "x2": 832, "y2": 36},
            {"type": "number", "x": 832, "y": 68, "text": "3"}
        ]
    },
    # 5. sign-documents
    {
        "id": "sign-documents",
        "task_id": "sign-documents",
        "title": "Sign documents",
        "source_image": "help/screenshots_clean/guide-signature-manager-light.png",
        "output_image": "guide-sign-documents-1.png",
        "caption": "Signature drawing canvas pad with baseline guide line.",
        "alt_text": "Signature modal dialog with trackpad drawing pad and insert button",
        "annotations": [
            {"type": "box", "x": 18, "y": 44, "w": 364, "h": 160},
            {"type": "arrow", "x1": 410, "y1": 120, "x2": 384, "y2": 120},
            {"type": "number", "x": 425, "y": 120, "text": "1"},
            {"type": "box", "x": 18, "y": 218, "w": 70, "h": 28},
            {"type": "arrow", "x1": 53, "y1": 265, "x2": 53, "y2": 248},
            {"type": "number", "x": 53, "y": 278, "text": "2"},
            {"type": "box", "x": 268, "y": 218, "w": 114, "h": 28},
            {"type": "arrow", "x1": 325, "y1": 265, "x2": 325, "y2": 248},
            {"type": "number", "x": 325, "y": 278, "text": "3"}
        ]
    },
    # 6. redact-content
    {
        "id": "redact-content",
        "task_id": "redact-content",
        "title": "Redact content",
        "source_image": "help/screenshots_clean/guide-markup-tools-light.png",
        "output_image": "guide-redact-content-1.png",
        "caption": "Redaction tool for blacking out confidential information.",
        "alt_text": "Redaction tool highlighted on the secondary Markup Toolbar",
        "annotations": [
            {"type": "box", "x": 272, "y": 4, "w": 32, "h": 30},
            {"type": "arrow", "x1": 288, "y1": 55, "x2": 288, "y2": 36},
            {"type": "number", "x": 288, "y": 68, "text": "1"},
            {"type": "blur", "x": 400, "y": 180, "w": 180, "h": 24},
            {"type": "box", "x": 398, "y": 178, "w": 184, "h": 28},
            {"type": "arrow", "x1": 490, "y1": 235, "x2": 490, "y2": 208},
            {"type": "number", "x": 490, "y": 248, "text": "2"}
        ]
    },
    # 7. adjust-color
    {
        "id": "adjust-color",
        "task_id": "adjust-color",
        "title": "Adjust color",
        "source_image": "help/screenshots_clean/guide-adjust-color-light.png",
        "output_image": "guide-adjust-color-1.png",
        "caption": "Real-time RGB histogram and image color adjustment sliders.",
        "alt_text": "Adjust color dialog with real-time histogram and exposure sliders",
        "annotations": [
            {"type": "box", "x": 16, "y": 16, "w": 308, "h": 84},
            {"type": "arrow", "x1": 345, "y1": 58, "x2": 326, "y2": 58},
            {"type": "number", "x": 360, "y": 58, "text": "1"},
            {"type": "box", "x": 16, "y": 110, "w": 140, "h": 28},
            {"type": "arrow", "x1": 86, "y1": 160, "x2": 86, "y2": 140},
            {"type": "number", "x": 86, "y": 172, "text": "2"},
            {"type": "box", "x": 16, "y": 190, "w": 308, "h": 220},
            {"type": "arrow", "x1": 345, "y1": 300, "x2": 326, "y2": 300},
            {"type": "number", "x": 360, "y": 300, "text": "3"}
        ]
    },
    # 8. adjust-size
    {
        "id": "adjust-size",
        "task_id": "adjust-size",
        "title": "Adjust size",
        "source_image": "help/screenshots_clean/guide-adjust-size-light.png",
        "output_image": "guide-adjust-size-1.png",
        "caption": "Adjust Size dialog with proportional scaling and resolution.",
        "alt_text": "Adjust Size dialog showing dimension inputs and aspect ratio lock",
        "annotations": [
            {"type": "box", "x": 18, "y": 38, "w": 354, "h": 32},
            {"type": "arrow", "x1": 395, "y1": 54, "x2": 374, "y2": 54},
            {"type": "number", "x": 410, "y": 54, "text": "1"},
            {"type": "box", "x": 18, "y": 80, "w": 354, "h": 110},
            {"type": "arrow", "x1": 395, "y1": 135, "x2": 374, "y2": 135},
            {"type": "number", "x": 410, "y": 135, "text": "2"},
            {"type": "box", "x": 18, "y": 200, "w": 200, "h": 24},
            {"type": "arrow", "x1": 240, "y1": 212, "x2": 220, "y2": 212},
            {"type": "number", "x": 255, "y": 212, "text": "3"}
        ]
    },
    # 9. organize-pdf-pages
    {
        "id": "organize-pdf-pages",
        "task_id": "organize-pdf-pages",
        "title": "Organize PDF pages",
        "source_image": "help/screenshots_clean/guide-sidebar-thumbnails-light.png",
        "output_image": "guide-organize-pdf-pages-1.png",
        "caption": "Reorder, duplicate, insert, or delete pages in sidebar.",
        "alt_text": "Thumbnail cards in sidebar for page reordering and context actions",
        "annotations": [
            {"type": "box", "x": 12, "y": 48, "w": 140, "h": 160},
            {"type": "arrow", "x1": 175, "y1": 120, "x2": 155, "y2": 120},
            {"type": "number", "x": 190, "y": 120, "text": "1"},
            {"type": "box", "x": 12, "y": 220, "w": 140, "h": 160},
            {"type": "arrow", "x1": 175, "y1": 290, "x2": 155, "y2": 290},
            {"type": "number", "x": 190, "y": 290, "text": "2"}
        ]
    },
    # 10. save-safely
    {
        "id": "save-safely",
        "task_id": "save-safely",
        "title": "Save safely",
        "source_image": "help/screenshots_clean/guide-toolbar-overview-light.png",
        "output_image": "guide-save-safely-1.png",
        "caption": "File save commands and unsaved edits confirmation prompt.",
        "alt_text": "Preview window demonstrating safe saving and revert features",
        "annotations": [
            {"type": "box", "x": 6, "y": 6, "w": 24, "h": 24},
            {"type": "arrow", "x1": 50, "y1": 50, "x2": 25, "y2": 25},
            {"type": "number", "x": 65, "y": 55, "text": "1"},
            {"type": "box", "x": 340, "y": 8, "w": 220, "h": 32},
            {"type": "arrow", "x1": 450, "y1": 65, "x2": 450, "y2": 42},
            {"type": "number", "x": 450, "y": 78, "text": "2"}
        ]
    },
    # 11. export-and-print
    {
        "id": "export-and-print",
        "task_id": "export-and-print",
        "title": "Export and print",
        "source_image": "help/screenshots_clean/guide-export-options-light.png",
        "output_image": "guide-export-and-print-1.png",
        "caption": "Export sheet format selection and resolution settings.",
        "alt_text": "Export dialog sheet with format choices and DPI resolution menu",
        "annotations": [
            {"type": "box", "x": 24, "y": 64, "w": 412, "h": 30},
            {"type": "arrow", "x1": 460, "y1": 79, "x2": 438, "y2": 79},
            {"type": "number", "x": 475, "y": 79, "text": "1"},
            {"type": "box", "x": 24, "y": 104, "w": 412, "h": 30},
            {"type": "arrow", "x1": 460, "y1": 119, "x2": 438, "y2": 119},
            {"type": "number", "x": 475, "y": 119, "text": "2"},
            {"type": "box", "x": 360, "y": 306, "w": 76, "h": 28},
            {"type": "arrow", "x1": 398, "y1": 275, "x2": 398, "y2": 302},
            {"type": "number", "x": 398, "y": 260, "text": "3"}
        ]
    },
    # 12. merge-and-split-pdfs
    {
        "id": "merge-and-split-pdfs",
        "task_id": "merge-and-split-pdfs",
        "title": "Merge and split PDFs",
        "source_image": "help/screenshots_clean/guide-sidebar-thumbnails-light.png",
        "output_image": "guide-merge-and-split-pdfs-1.png",
        "caption": "Merge multiple documents or extract page ranges.",
        "alt_text": "Thumbnail multi-page view for splitting and merging PDF files",
        "annotations": [
            {"type": "box", "x": 10, "y": 6, "w": 148, "h": 28},
            {"type": "arrow", "x1": 180, "y1": 20, "x2": 160, "y2": 20},
            {"type": "number", "x": 195, "y": 20, "text": "1"},
            {"type": "box", "x": 12, "y": 48, "w": 140, "h": 340},
            {"type": "arrow", "x1": 185, "y1": 210, "x2": 155, "y2": 210},
            {"type": "number", "x": 200, "y": 210, "text": "2"}
        ]
    },
    # 13. password-and-encryption
    {
        "id": "password-and-encryption",
        "task_id": "password-and-encryption",
        "title": "Password and encryption",
        "source_image": "help/screenshots_clean/guide-inspector-panel-light.png",
        "output_image": "guide-password-and-encryption-1.png",
        "caption": "Document security status and metadata inspector.",
        "alt_text": "Inspector panel showing PDF document security and encryption details",
        "annotations": [
            {"type": "box", "x": 14, "y": 40, "w": 332, "h": 280},
            {"type": "arrow", "x1": 365, "y1": 160, "x2": 348, "y2": 160},
            {"type": "number", "x": 380, "y": 160, "text": "1"}
        ]
    }
]

out_dir = "help/content/image_guide"
os.makedirs(out_dir, exist_ok=True)
for spec in specs:
    fname = os.path.join(out_dir, f"{spec['id'].replace('-', '_')}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    print(f"Wrote {fname}")
print(f"Successfully generated {len(specs)} image guide specs.")
