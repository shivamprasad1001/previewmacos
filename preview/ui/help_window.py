"""
Preview Help Window — Authentic Apple Support / macOS User Guide documentation system.
Features:
- Left navigation tree with top search filter.
- Clean right-hand content pane (max 720px width).
- Strict visual style: plain white/dark theme, system font (Inter/SF), no gradients, no shadows.
- Keyboard shortcuts badges (<kbd>Ctrl + S</kbd>).
- Data-driven: reads all content from help/content/ (Get Started, Tasks, Dictionary, Image Guide, PDF Guide, Shortcuts, Troubleshooting, About).
- Shortcuts: F1 opens Help, Ctrl+F focuses search, Esc closes.
"""

import os
import json
import shutil
import subprocess
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QTextBrowser,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QDesktopServices

from preview.icons import MacIconFactory
from preview.theme import MacTheme


class HelpWindow(QDialog):
    """macOS / Apple Support styled documentation viewer."""

    def __init__(self, theme: MacTheme = MacTheme.DARK, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Preview Help")
        self.resize(1080, 720)
        self.setMinimumSize(850, 550)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinMaxButtonsHint)

        self.current_theme = theme
        self.content_dir = self._find_content_dir()
        self.all_dictionary_entries: List[Dict[str, Any]] = []
        self.current_page_id: str = "what-is-preview"

        self._load_data()
        self._setup_ui()
        self._apply_theme()
        self._setup_shortcuts()

        # Initial selection
        self.navigate_to("what-is-preview")

    def _find_content_dir(self) -> str:
        candidates = [
            os.path.abspath("help/content"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "help", "content"),
            "/run/media/zoro0x1/Hard Disk Drive/MyPrograms/REA/preview-macos/help/content"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return os.path.abspath("help/content")

    def _load_data(self):
        dict_path = os.path.join(self.content_dir, "dictionary.json")
        if os.path.exists(dict_path):
            try:
                with open(dict_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.all_dictionary_entries = data.get("entries", [])
            except Exception:
                self.all_dictionary_entries = []

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setHandleWidth(1)

        # --- Left Sidebar (Search + Tree) ---
        left_widget = QWidget()
        left_widget.setMinimumWidth(240)
        left_widget.setMaximumWidth(380)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 14, 12, 14)
        left_layout.setSpacing(10)

        # Search Bar
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("helpSearchInput")
        self.search_edit.setPlaceholderText("Search Help (Ctrl+F)")
        self.search_edit.setFixedHeight(28)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_edit)
        left_layout.addLayout(search_row)

        # Navigation Tree
        self.nav_tree = QTreeWidget()
        self.nav_tree.setObjectName("helpNavTree")
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setAnimated(True)
        self.nav_tree.itemClicked.connect(self._on_tree_item_clicked)
        left_layout.addWidget(self.nav_tree)

        self._populate_tree()

        self.splitter.addWidget(left_widget)

        # --- Right Content Pane ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.browser = QTextBrowser()
        self.browser.setObjectName("helpContentBrowser")
        self.browser.setOpenExternalLinks(False)
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self._on_anchor_clicked)
        right_layout.addWidget(self.browser)

        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([280, 800])

        main_layout.addWidget(self.splitter)

    def _setup_shortcuts(self):
        # Ctrl+F to focus search input
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._focus_search)

        # Esc closes dialog
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self.close)

    def _focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _populate_tree(self):
        self.nav_tree.clear()

        # 1. Get Started
        item_get_started = QTreeWidgetItem(self.nav_tree, ["Get Started"])
        item_get_started.setData(0, Qt.ItemDataRole.UserRole, "header")
        
        sub_what = QTreeWidgetItem(item_get_started, ["What is Preview"])
        sub_what.setData(0, Qt.ItemDataRole.UserRole, "what-is-preview")
        
        sub_open = QTreeWidgetItem(item_get_started, ["Open a file or folder"])
        sub_open.setData(0, Qt.ItemDataRole.UserRole, "open-file-or-folder")
        
        sub_window = QTreeWidgetItem(item_get_started, ["Window overview"])
        sub_window.setData(0, Qt.ItemDataRole.UserRole, "window-overview")
        
        item_get_started.setExpanded(True)

        # 2. Help Dictionary
        item_dict = QTreeWidgetItem(self.nav_tree, ["Help Dictionary"])
        item_dict.setData(0, Qt.ItemDataRole.UserRole, "dictionary")

        # 3. Tasks
        item_tasks = QTreeWidgetItem(self.nav_tree, ["Tasks"])
        item_tasks.setData(0, Qt.ItemDataRole.UserRole, "header")

        tasks_list = [
            ("View and navigate documents", "view-and-navigate"),
            ("Use the sidebar", "use-the-sidebar"),
            ("Annotate and mark up", "annotate-and-markup"),
            ("Select, crop and rotate", "select-crop-and-rotate"),
            ("Sign documents", "sign-documents"),
            ("Redact content", "redact-content"),
            ("Adjust color", "adjust-color"),
            ("Adjust size", "adjust-size"),
            ("Organize PDF pages", "organize-pdf-pages"),
            ("Save safely", "save-safely"),
            ("Export and print", "export-and-print"),
            ("Merge and split PDFs", "merge-and-split-pdfs"),
            ("Password and encryption", "password-and-encryption")
        ]
        for label, tid in tasks_list:
            titem = QTreeWidgetItem(item_tasks, [label])
            titem.setData(0, Qt.ItemDataRole.UserRole, tid)

        item_tasks.setExpanded(True)

        # 4. Image Guide
        item_image_guide = QTreeWidgetItem(self.nav_tree, ["Image Guide"])
        item_image_guide.setData(0, Qt.ItemDataRole.UserRole, "image-guide")

        # 5. PDF Guide
        item_pdf_guide = QTreeWidgetItem(self.nav_tree, ["PDF Guide"])
        item_pdf_guide.setData(0, Qt.ItemDataRole.UserRole, "pdf-guide")

        # 6. Keyboard Shortcuts
        item_shortcuts = QTreeWidgetItem(self.nav_tree, ["Keyboard Shortcuts"])
        item_shortcuts.setData(0, Qt.ItemDataRole.UserRole, "shortcuts")

        # 7. Troubleshooting
        item_trouble = QTreeWidgetItem(self.nav_tree, ["Troubleshooting"])
        item_trouble.setData(0, Qt.ItemDataRole.UserRole, "troubleshooting")

        # 8. About and Updates
        item_about = QTreeWidgetItem(self.nav_tree, ["About and Updates"])
        item_about.setData(0, Qt.ItemDataRole.UserRole, "about-and-updates")

    def _apply_theme(self):
        is_dark = (self.current_theme == MacTheme.DARK)
        bg_col = "#1e1e1e" if is_dark else "#ffffff"
        side_bg = "#252526" if is_dark else "#f7f7f8"
        text_col = "#f5f5f7" if is_dark else "#1d1d1f"
        border_col = "#38383a" if is_dark else "#e5e5ea"
        input_bg = "#2c2c2e" if is_dark else "#ffffff"
        input_border = "#48484a" if is_dark else "#d2d2d7"
        sel_bg = "#007aff" if is_dark else "#0a84ff"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: {text_col};
            }}
            QSplitter::handle {{
                background-color: {border_col};
            }}
            QLineEdit#helpSearchInput {{
                background-color: {input_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_col};
                font-size: 13px;
                font-family: -apple-system, "SF Pro Text", "Inter", sans-serif;
            }}
            QLineEdit#helpSearchInput:focus {{
                border: 1.5px solid {sel_bg};
            }}
            QTreeWidget#helpNavTree {{
                background-color: {side_bg};
                border: none;
                color: {text_col};
                font-size: 13px;
                font-family: -apple-system, "SF Pro Text", "Inter", sans-serif;
                outline: none;
            }}
            QTreeWidget#helpNavTree::item {{
                padding: 5px 6px;
                border-radius: 4px;
            }}
            QTreeWidget#helpNavTree::item:hover {{
                background-color: {'rgba(255,255,255,0.06)' if is_dark else 'rgba(0,0,0,0.05)'};
            }}
            QTreeWidget#helpNavTree::item:selected {{
                background-color: {sel_bg};
                color: #ffffff;
                font-weight: 600;
            }}
            QTextBrowser#helpContentBrowser {{
                background-color: {bg_col};
                border: none;
                padding: 24px 36px;
                color: {text_col};
            }}
        """)

    def _on_search_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_tree()
            self.navigate_to(self.current_page_id)
            return

        # If user searches, switch to Dictionary search mode or filter items
        self.navigate_to("dictionary", filter_text=query)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id and node_id != "header":
            self.navigate_to(node_id)

    def _on_anchor_clicked(self, url: QUrl):
        target = url.toString()
        if target.startswith("entry:"):
            entry_id = target.split(":", 1)[1]
            self.navigate_to("dictionary", filter_text=entry_id)
        elif target.startswith("topic:"):
            topic_id = target.split(":", 1)[1]
            self.navigate_to(topic_id)
        elif target.startswith("action:"):
            action = target.split(":", 1)[1]
            if action == "save_pdf_guide":
                self._save_pdf_guide()
            elif action == "print_pdf_guide":
                self._print_pdf_guide()
            elif action == "save_cheat_sheet":
                self._save_cheat_sheet()
        elif target.startswith("http://") or target.startswith("https://"):
            QDesktopServices.openUrl(url)

    def navigate_to(self, page_id: str, filter_text: str = ""):
        self.current_page_id = page_id
        
        # Highlight in tree if exists
        self._select_tree_item(page_id)

        html = ""
        if page_id in ["what-is-preview", "open-file-or-folder", "window-overview"]:
            html = self._render_get_started_html(page_id)
        elif page_id == "dictionary":
            html = self._render_dictionary_html(filter_text)
        elif page_id in [
            "view-and-navigate", "use-the-sidebar", "annotate-and-markup",
            "select-crop-and-rotate", "sign-documents", "redact-content",
            "adjust-color", "adjust-size", "organize-pdf-pages",
            "save-safely", "export-and-print", "merge-and-split-pdfs",
            "password-and-encryption"
        ]:
            html = self._render_task_html(page_id)
        elif page_id == "image-guide":
            html = self._render_image_guide_html()
        elif page_id == "pdf-guide":
            html = self._render_pdf_guide_html()
        elif page_id == "shortcuts":
            html = self._render_shortcuts_html()
        elif page_id == "troubleshooting":
            html = self._render_troubleshooting_html()
        elif page_id == "about-and-updates":
            html = self._render_about_html()
        else:
            html = self._render_get_started_html("what-is-preview")

        self.browser.setHtml(html)

    def _select_tree_item(self, node_id: str):
        def search(item: QTreeWidgetItem):
            if item.data(0, Qt.ItemDataRole.UserRole) == node_id:
                self.nav_tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if search(item.child(i)):
                    return True
            return False

        for i in range(self.nav_tree.topLevelItemCount()):
            if search(self.nav_tree.topLevelItem(i)):
                break

    def open_shortcuts(self):
        """Opens directly to the Keyboard Shortcuts page."""
        self.navigate_to("shortcuts")

    def open_entry(self, entry_id: str):
        """Navigates directly to a matching dictionary entry."""
        self.navigate_to("dictionary", filter_text=entry_id)

    # --- HTML Page Renderers adhering strictly to visual style ---

    def _get_base_css(self) -> str:
        is_dark = (self.current_theme == MacTheme.DARK)
        bg = "#1e1e1e" if is_dark else "#ffffff"
        text = "#f5f5f7" if is_dark else "#1d1d1f"
        subtext = "#8e8e93" if is_dark else "#6e6e73"
        divider = "#38383a" if is_dark else "#e5e5ea"
        link = "#2997ff" if is_dark else "#0066cc"
        kbd_bg = "#2c2c2e" if is_dark else "#f5f5f7"
        kbd_border = "#48484a" if is_dark else "#d2d2d7"
        kbd_text = "#f5f5f7" if is_dark else "#1d1d1f"
        note_bg = "rgba(255,255,255,0.04)" if is_dark else "#fbfbfd"
        card_border = "#38383a" if is_dark else "#d2d2d7"

        return f"""
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", "Segoe UI", sans-serif;
                font-size: 14px;
                line-height: 1.5;
                color: {text};
                background-color: {bg};
                margin: 0;
                padding: 0;
            }}
            .wrapper {{
                max-width: 720px;
                margin: 0 auto;
            }}
            h1 {{
                font-size: 24px;
                font-weight: 700;
                color: {text};
                margin: 0 0 8px 0;
            }}
            h2 {{
                font-size: 16px;
                font-weight: 700;
                color: {text};
                margin: 24px 0 8px 0;
            }}
            h3 {{
                font-size: 14px;
                font-weight: 700;
                color: {text};
                margin: 16px 0 6px 0;
            }}
            p {{
                margin: 0 0 12px 0;
            }}
            .summary {{
                font-size: 14px;
                color: {subtext};
                margin-bottom: 16px;
            }}
            hr {{
                border: none;
                border-top: 1px solid {divider};
                margin: 16px 0 20px 0;
            }}
            ol, ul {{
                margin: 0 0 16px 0;
                padding-left: 22px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            a {{
                color: {link};
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            kbd {{
                display: inline-block;
                background-color: {kbd_bg};
                border: 1px solid {kbd_border};
                border-radius: 4px;
                padding: 1px 6px;
                font-family: monospace;
                font-size: 12px;
                font-weight: 600;
                color: {kbd_text};
                white-space: nowrap;
            }}
            .note-box {{
                background-color: {note_bg};
                border-left: 3px solid {divider};
                padding: 10px 14px;
                margin: 16px 0;
                font-size: 13px;
                color: {subtext};
            }}
            .dict-entry {{
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 1px solid {divider};
            }}
            .dict-meta {{
                font-size: 13px;
                color: {subtext};
                margin-bottom: 8px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 16px 0;
            }}
            th {{
                text-align: left;
                font-size: 12px;
                font-weight: 700;
                color: {subtext};
                border-bottom: 1px solid {divider};
                padding: 6px 10px;
            }}
            td {{
                font-size: 13px;
                border-bottom: 1px solid {divider};
                padding: 8px 10px;
            }}
            .btn-action {{
                display: inline-block;
                background-color: {link};
                color: #ffffff !important;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                margin-right: 8px;
                text-decoration: none;
            }}
            .image-card {{
                margin: 20px 0;
                border: 1px solid {card_border};
                border-radius: 6px;
                padding: 8px;
                background: {bg};
            }}
            .caption {{
                font-size: 12px;
                color: {subtext};
                margin-top: 6px;
                text-align: center;
            }}
        </style>
        """

    def _render_get_started_html(self, page_id: str) -> str:
        fname = os.path.join(self.content_dir, "get_started", f"{page_id.replace('-', '_')}.json")
        data = {}
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

        title = data.get("title", "Get Started")
        summary = data.get("summary", "")
        sections = data.get("sections", [])
        steps = data.get("steps", [])
        note = data.get("note", "")
        related = data.get("related", [])

        sec_html = "".join([f"<h2>{s.get('heading', '')}</h2><p>{s.get('text', '')}</p>" for s in sections])
        steps_html = "".join([f"<li>{s}</li>" for s in steps])
        related_html = " | ".join([f'<a href="topic:{r}">{r.replace("-", " ").title()}</a>' for r in related])

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>{title}</h1>
                <div class="summary">{summary}</div>
                <hr/>
                {sec_html}
                <h2>Steps</h2>
                <ol>{steps_html}</ol>
                {f'<div class="note-box">Note: {note}</div>' if note else ''}
                <h2>Related topics</h2>
                <p>{related_html}</p>
            </div>
        </body>
        </html>
        """

    def _render_task_html(self, task_id: str) -> str:
        fname = os.path.join(self.content_dir, "tasks", f"{task_id.replace('-', '_')}.json")
        data = {}
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

        title = data.get("title", "Task")
        summary = data.get("summary", "")
        sections = data.get("sections", [])
        steps = data.get("steps", [])
        note = data.get("note", "")
        related = data.get("related", [])

        sec_html = "".join([f"<h2>{s.get('heading', '')}</h2><p>{s.get('text', '')}</p>" for s in sections])
        steps_html = "".join([f"<li>{s}</li>" for s in steps])
        related_html = " | ".join([f'<a href="topic:{r}">{r.replace("-", " ").title()}</a>' for r in related])

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>{title}</h1>
                <div class="summary">{summary}</div>
                <hr/>
                {sec_html}
                <h2>How to use</h2>
                <ol>{steps_html}</ol>
                {f'<div class="note-box">Note: {note}</div>' if note else ''}
                <h2>Related topics</h2>
                <p>{related_html}</p>
            </div>
        </body>
        </html>
        """

    def _render_dictionary_html(self, filter_text: str = "") -> str:
        query = filter_text.lower().strip()
        filtered = self.all_dictionary_entries
        if query:
            filtered = [
                e for e in self.all_dictionary_entries
                if query in e.get("name", "").lower()
                or query in e.get("id", "").lower()
                or query in e.get("meaning", "").lower()
                or query in e.get("where", "").lower()
            ]

        # Group by letter
        by_letter: Dict[str, List[Dict[str, Any]]] = {}
        for e in filtered:
            letter = e.get("letter", e.get("name", "A")[:1].upper())
            by_letter.setdefault(letter, []).append(e)

        entries_html = ""
        for letter in sorted(by_letter.keys()):
            entries_html += f"<h2>{letter}</h2><hr/>"
            for item in by_letter[letter]:
                name = item.get("name", "")
                meaning = item.get("meaning", "")
                where = item.get("where", "")
                shortcut = item.get("shortcut", "")
                steps = item.get("steps", [])
                related = item.get("related", [])

                steps_li = "".join([f"<li>{s}</li>" for s in steps])
                rel_links = " | ".join([f'<a href="entry:{r}">{r.replace("-", " ").title()}</a>' for r in related])

                kbd_badge = f'<kbd>{shortcut}</kbd>' if shortcut else ''

                entries_html += f"""
                <div class="dict-entry" id="{item.get('id', '')}">
                    <h3>{name} {kbd_badge}</h3>
                    <p><b>Meaning:</b> {meaning}</p>
                    <div class="dict-meta"><b>Where:</b> {where}</div>
                    <ol>{steps_li}</ol>
                    {f'<div class="dict-meta"><b>Related:</b> {rel_links}</div>' if rel_links else ''}
                </div>
                """

        if not filtered:
            entries_html = f"<p>No matching dictionary entries found for &ldquo;{filter_text}&rdquo;.</p>"

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>Help Dictionary</h1>
                <div class="summary">Alphabetical A-Z guide of every tool, feature, menu item, and term. Showing {len(filtered)} of {len(self.all_dictionary_entries)} entries.</div>
                <hr/>
                {entries_html}
            </div>
        </body>
        </html>
        """

    def _render_image_guide_html(self) -> str:
        # Load image guide specs
        specs_dir = os.path.join(self.content_dir, "image_guide")
        specs = []
        if os.path.exists(specs_dir):
            for f in sorted(os.listdir(specs_dir)):
                if f.endswith(".json"):
                    with open(os.path.join(specs_dir, f), "r", encoding="utf-8") as sfile:
                        specs.append(json.load(sfile))

        items_html = ""
        base_dir = os.path.abspath(".")
        for spec in specs:
            title = spec.get("title", "")
            caption = spec.get("caption", "")
            alt_text = spec.get("alt_text", "")
            out_img = spec.get("output_image", "")
            img_path = os.path.join(base_dir, "help", "generated", out_img)

            items_html += f"""
            <h2>{title}</h2>
            <div class="image-card">
                <img src="file://{img_path}" width="100%" alt="{alt_text}" style="border-radius: 4px; display: block;" />
                <div class="caption">{caption}</div>
            </div>
            """

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>Image Guide</h1>
                <div class="summary">Annotated real screenshots showing every task with numbered steps, directional arrows, and tool highlights.</div>
                <hr/>
                {items_html}
            </div>
        </body>
        </html>
        """

    def _render_pdf_guide_html(self) -> str:
        guide_path = os.path.abspath("help/generated/preview_user_guide.pdf")
        sheet_path = os.path.abspath("help/generated/preview_shortcuts_cheatsheet.pdf")

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>PDF User Guide & Cheat Sheet</h1>
                <div class="summary">Calm, publication-ready A4 documentation generated with PyMuPDF. Pure black text on white without decorative color blocks.</div>
                <hr/>
                <h2>Available Documents</h2>
                <p>
                    <a href="action:save_pdf_guide" class="btn-action">Save User Guide as PDF</a>
                    <a href="action:save_cheat_sheet" class="btn-action">Download Shortcut Cheat Sheet</a>
                    <a href="action:print_pdf_guide" class="btn-action">Print Guide</a>
                </p>
                <h2>Guide Contents</h2>
                <ul>
                    <li><b>Cover:</b> Name, version, publication date, and attribution.</li>
                    <li><b>Quick Start:</b> 5 simple steps to get started immediately.</li>
                    <li><b>Window Overview:</b> Detailed breakdown of Menubar, Toolbar, Sidebar, and Canvas.</li>
                    <li><b>Feature Table:</b> Complete reference table of menus, tools, and shortcuts.</li>
                    <li><b>Shortcuts:</b> Categorized hotkeys reference.</li>
                    <li><b>Common Problems & Fixes:</b> Practical troubleshooting solutions.</li>
                </ul>
                <div class="note-box">
                    Files are saved in <code>help/generated/</code>:
                    <br/>• User Guide: <code>preview_user_guide.pdf</code> (5 pages A4)
                    <br/>• Cheat Sheet: <code>preview_shortcuts_cheatsheet.pdf</code> (1 page A4)
                </div>
            </div>
        </body>
        </html>
        """

    def _render_shortcuts_html(self) -> str:
        fname = os.path.join(self.content_dir, "shortcuts.json")
        data = {}
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

        title = data.get("title", "Keyboard Shortcuts")
        summary = data.get("summary", "")
        categories = data.get("categories", [])
        note = data.get("note", "")

        tables_html = ""
        for cat in categories:
            cname = cat.get("name", "")
            s_list = cat.get("shortcuts", [])
            rows_html = "".join([f"<tr><td>{s['action']}</td><td><kbd>{s['key']}</kbd></td></tr>" for s in s_list])
            tables_html += f"""
            <h2>{cname}</h2>
            <table>
                <thead>
                    <tr><th>Action</th><th style="width: 220px;">Shortcut Badge</th></tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>{title}</h1>
                <div class="summary">{summary}</div>
                <hr/>
                {tables_html}
                {f'<div class="note-box">Note: {note}</div>' if note else ''}
            </div>
        </body>
        </html>
        """

    def _render_troubleshooting_html(self) -> str:
        fname = os.path.join(self.content_dir, "troubleshooting.json")
        data = {}
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

        title = data.get("title", "Troubleshooting")
        summary = data.get("summary", "")
        items = data.get("items", [])
        note = data.get("note", "")

        trouble_html = ""
        for it in items:
            prob = it.get("problem", "")
            cause = it.get("cause", "")
            sol = it.get("solution", [])
            sol_li = "".join([f"<li>{s}</li>" for s in sol])
            trouble_html += f"""
            <h3>{prob}</h3>
            <p><b>Cause:</b> {cause}</p>
            <ol>{sol_li}</ol>
            <hr/>
            """

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>{title}</h1>
                <div class="summary">{summary}</div>
                <hr/>
                {trouble_html}
                {f'<div class="note-box">Note: {note}</div>' if note else ''}
            </div>
        </body>
        </html>
        """

    def _render_about_html(self) -> str:
        fname = os.path.join(self.content_dir, "about_and_updates.json")
        data = {}
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

        title = data.get("title", "About and Updates")
        summary = data.get("summary", "")
        sections = data.get("sections", [])
        steps = data.get("steps", [])
        note = data.get("note", "")

        sec_html = "".join([f"<h2>{s.get('heading', '')}</h2><p>{s.get('text', '')}</p>" for s in sections])
        steps_html = "".join([f"<li>{s}</li>" for s in steps])

        return f"""
        <html>
        <head>{self._get_base_css()}</head>
        <body>
            <div class="wrapper">
                <h1>{title}</h1>
                <div class="summary">{summary}</div>
                <hr/>
                {sec_html}
                <h2>How to check for updates</h2>
                <ol>{steps_html}</ol>
                {f'<div class="note-box">Note: {note}</div>' if note else ''}
            </div>
        </body>
        </html>
        """

    # --- Actions for PDF Guide ---

    def _save_pdf_guide(self):
        src = os.path.abspath("help/generated/preview_user_guide.pdf")
        if not os.path.exists(src):
            QMessageBox.warning(self, "PDF Missing", "PDF guide has not been generated yet.")
            return

        dest, _ = QFileDialog.getSaveFileName(self, "Save User Guide as PDF", "Preview_for_Linux_User_Guide.pdf", "PDF Documents (*.pdf)")
        if dest:
            try:
                shutil.copy(src, dest)
                QMessageBox.information(self, "Saved", f"User Guide successfully saved to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _save_cheat_sheet(self):
        src = os.path.abspath("help/generated/preview_shortcuts_cheatsheet.pdf")
        if not os.path.exists(src):
            QMessageBox.warning(self, "File Missing", "Cheat sheet has not been generated yet.")
            return

        dest, _ = QFileDialog.getSaveFileName(self, "Save Shortcuts Cheat Sheet", "Preview_Shortcuts_Cheat_Sheet.pdf", "PDF Documents (*.pdf)")
        if dest:
            try:
                shutil.copy(src, dest)
                QMessageBox.information(self, "Saved", f"Cheat sheet successfully saved to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _print_pdf_guide(self):
        src = os.path.abspath("help/generated/preview_user_guide.pdf")
        if not os.path.exists(src):
            QMessageBox.warning(self, "File Missing", "PDF guide file not found.")
            return

        # Open in default system PDF viewer for printing
        QDesktopServices.openUrl(QUrl.fromLocalFile(src))
