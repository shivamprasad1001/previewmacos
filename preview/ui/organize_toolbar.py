"""
macOS style Organize Action Bar for Mode C: Page and Document Management.
Exposes page rotation, insertion, deletion, duplication, merging, and splitting.
"""

from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QToolButton, QLabel, QFrame, QSizePolicy
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal

from preview.icons import MacIconFactory, Icon


class OrganizeActionBar(QWidget):
    """Secondary toolbar active during Mode C (Organize), 44px height matching design spec."""

    rotate_left_requested = pyqtSignal()
    rotate_right_requested = pyqtSignal()
    duplicate_page_requested = pyqtSignal()
    insert_blank_requested = pyqtSignal()
    insert_file_requested = pyqtSignal()
    delete_page_requested = pyqtSignal()
    merge_requested = pyqtSignal()
    split_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("organizeActionBar")
        self.setFixedHeight(44)
        self._theme_col: str = "#f5f5f7"

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(8)

        title = QLabel("Page Management:")
        title.setStyleSheet("font-size: 11px; font-weight: 600; color: #98989d; padding-right: 4px;")
        layout.addWidget(title)

        # Group 1: Page Rotation
        self.rot_left_btn = QToolButton()
        self.rot_left_btn.setText("Rotate Left")
        self.rot_left_btn.setToolTip("Rotate Page 90° Left (Ctrl+L)")
        self.rot_left_btn.setAccessibleName("Rotate Page 90° Left (Ctrl+L)")
        self.rot_left_btn.setAccessibleDescription("Rotate active page counter-clockwise")
        self.rot_left_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.rot_left_btn.setFixedHeight(32)
        self.rot_left_btn.clicked.connect(self.rotate_left_requested.emit)

        self.rot_right_btn = QToolButton()
        self.rot_right_btn.setText("Rotate Right")
        self.rot_right_btn.setToolTip("Rotate Page 90° Right (Ctrl+R)")
        self.rot_right_btn.setAccessibleName("Rotate Page 90° Right (Ctrl+R)")
        self.rot_right_btn.setAccessibleDescription("Rotate active page clockwise")
        self.rot_right_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.rot_right_btn.setFixedHeight(32)
        self.rot_right_btn.clicked.connect(self.rotate_right_requested.emit)

        self.group_rotate = self._create_group([self.rot_left_btn, self.rot_right_btn])
        layout.addWidget(self.group_rotate)
        layout.addWidget(self._create_divider())

        # Group 2: Page Operations
        self.dup_btn = QToolButton()
        self.dup_btn.setText("Duplicate")
        self.dup_btn.setToolTip("Duplicate Selected Page")
        self.dup_btn.setAccessibleName("Duplicate Selected Page")
        self.dup_btn.setAccessibleDescription("Duplicate current page")
        self.dup_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.dup_btn.setFixedHeight(32)
        self.dup_btn.clicked.connect(self.duplicate_page_requested.emit)

        self.insert_blank_btn = QToolButton()
        self.insert_blank_btn.setText("Insert Blank")
        self.insert_blank_btn.setToolTip("Insert Blank Page After Active Page")
        self.insert_blank_btn.setAccessibleName("Insert Blank Page")
        self.insert_blank_btn.setAccessibleDescription("Insert a blank page")
        self.insert_blank_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.insert_blank_btn.setFixedHeight(32)
        self.insert_blank_btn.clicked.connect(self.insert_blank_requested.emit)

        self.insert_file_btn = QToolButton()
        self.insert_file_btn.setText("Insert from File...")
        self.insert_file_btn.setToolTip("Insert Pages from PDF or Image (Ctrl+Shift+I)")
        self.insert_file_btn.setAccessibleName("Insert from File")
        self.insert_file_btn.setAccessibleDescription("Insert pages from external document")
        self.insert_file_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.insert_file_btn.setFixedHeight(32)
        self.insert_file_btn.clicked.connect(self.insert_file_requested.emit)

        self.del_btn = QToolButton()
        self.del_btn.setText("Delete Page")
        self.del_btn.setToolTip("Delete Active Page (Delete key)")
        self.del_btn.setAccessibleName("Delete Active Page")
        self.del_btn.setAccessibleDescription("Delete active page from document")
        self.del_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.del_btn.setFixedHeight(32)
        self.del_btn.setStyleSheet("color: #ff453a; font-weight: 550;")
        self.del_btn.clicked.connect(self.delete_page_requested.emit)

        self.group_pages = self._create_group([
            self.dup_btn, self.insert_blank_btn, self.insert_file_btn, self.del_btn
        ])
        layout.addWidget(self.group_pages)
        layout.addWidget(self._create_divider())

        layout.addStretch()

        # Group 3: Document Operations
        self.merge_btn = QToolButton()
        self.merge_btn.setText("Merge PDFs...")
        self.merge_btn.setToolTip("Combine multiple PDF documents")
        self.merge_btn.setAccessibleName("Merge PDFs")
        self.merge_btn.setAccessibleDescription("Combine multiple PDF documents into one")
        self.merge_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.merge_btn.setFixedHeight(32)
        self.merge_btn.clicked.connect(self.merge_requested.emit)

        self.split_btn = QToolButton()
        self.split_btn.setText("Split PDF...")
        self.split_btn.setToolTip("Extract pages or split into separate documents")
        self.split_btn.setAccessibleName("Split PDF")
        self.split_btn.setAccessibleDescription("Extract pages or split into separate files")
        self.split_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.split_btn.setFixedHeight(32)
        self.split_btn.clicked.connect(self.split_requested.emit)

        self.export_btn = QToolButton()
        self.export_btn.setText("Export...")
        self.export_btn.setToolTip("Export All Pages (Ctrl+E)")
        self.export_btn.setAccessibleName("Export All Pages")
        self.export_btn.setAccessibleDescription("Export all pages to PDF or image series")
        self.export_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.export_btn.setFixedHeight(32)
        self.export_btn.clicked.connect(self.export_requested.emit)

        self.group_doc = self._create_group([self.merge_btn, self.split_btn, self.export_btn])
        layout.addWidget(self.group_doc)

        self.update_icons(self._theme_col)

    def _create_group(self, buttons: List[QToolButton]) -> QFrame:
        group_frame = QFrame()
        group_frame.setObjectName("markupGroup")
        group_frame.setFixedHeight(34)
        group_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        glay = QHBoxLayout(group_frame)
        glay.setContentsMargins(1, 1, 1, 1)
        glay.setSpacing(2)
        for b in buttons:
            glay.addWidget(b)
        return group_frame

    def _create_divider(self) -> QWidget:
        sep = QWidget()
        sep.setObjectName("markupGroupSeparator")
        sep.setFixedSize(1, 20)
        return sep

    def update_icons(self, color_hex: str):
        self._theme_col = color_hex
        self.rot_left_btn.setIcon(MacIconFactory.create_icon("rotate_left", color_hex, 18))
        self.rot_right_btn.setIcon(MacIconFactory.create_icon("rotate_right", color_hex, 18))
        self.dup_btn.setIcon(MacIconFactory.create_icon("duplicate", color_hex, 18))
        self.insert_blank_btn.setIcon(MacIconFactory.create_icon("file-plus-2", color_hex, 18))
        self.insert_file_btn.setIcon(MacIconFactory.create_icon("file-up", color_hex, 18))
        self.del_btn.setIcon(MacIconFactory.create_icon("trash", "#ff453a", 18))
        self.merge_btn.setIcon(MacIconFactory.create_icon("merge", color_hex, 18))
        self.split_btn.setIcon(MacIconFactory.create_icon("split", color_hex, 18))
        self.export_btn.setIcon(MacIconFactory.create_icon("export", color_hex, 18))
