"""
macOS style collapsible left sidebar with page thumbnails and table of contents outline.
Features a custom thumbnail delegate replicating Apple Preview's page cards & badges.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QTreeWidget, QTreeWidgetItem, QLabel, QStackedWidget, QToolButton,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle, QMenu, QMessageBox, QSlider
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QModelIndex, QEvent

from preview.core.document import Document
from preview.icons import MacIconFactory

class MacThumbnailDelegate(QStyledItemDelegate):
    """Custom delegate rendering 4px radius thumbnail cards, 3px accent selection rings, and page pills."""

    def __init__(self, sidebar: 'MacSidebar'):
        super().__init__(sidebar)
        self.sidebar = sidebar

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        doc = self.sidebar.document
        if not doc:
            painter.restore()
            return

        page_idx = index.row()
        thumb_w = float(getattr(self.sidebar, "thumbnail_width", 110))
        pix = doc.get_thumbnail(page_idx, width=int(thumb_w))
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        r = option.rect

        # 1. Background hover highlight (subtle rounded card)
        if is_hovered and not is_selected:
            painter.setBrush(QBrush(QColor(255, 255, 255, 12)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(r).adjusted(4, 2, -4, -2), 6, 6)

        # 2. Compute thumbnail picture rect centered in top portion
        pw, ph = pix.width(), pix.height()
        max_pw, max_ph = thumb_w, thumb_w * 1.25
        scale = min(max_pw / max(1, pw), max_ph / max(1, ph))
        draw_w = pw * scale
        draw_h = ph * scale

        pic_x = r.left() + (r.width() - draw_w) / 2.0
        pic_y = r.top() + 8.0 + (max_ph - draw_h) / 2.0
        pic_rect = QRectF(pic_x, pic_y, draw_w, draw_h)

        # 3. Draw subtle paper drop shadow
        shadow_rect = pic_rect.adjusted(-1.0, 1.0, 1.0, 3.0)
        painter.setBrush(QBrush(QColor(0, 0, 0, 45)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 4.0, 4.0)

        # 4. Draw thumbnail image with 4px radius
        clip_path = QPainterPath()
        clip_path.addRoundedRect(pic_rect, 4.0, 4.0)
        painter.save()
        painter.setClipPath(clip_path)
        painter.drawPixmap(pic_rect.toRect(), pix)
        painter.restore()

        # 5. Draw 3px accent-colored selection ring or subtle border
        is_dark = getattr(self.sidebar.window(), "current_theme", "dark") == "dark"
        if is_selected:
            # 3px accent-colored selection ring with 4px radius
            sel_ring = pic_rect.adjusted(-2.0, -2.0, 2.0, 2.0)
            painter.setPen(QPen(QColor("#0a84ff"), 3.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(sel_ring, 4.0, 4.0)
        else:
            border_col = QColor(255, 255, 255, 30) if is_dark else QColor(0, 0, 0, 35)
            painter.setPen(QPen(border_col, 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(pic_rect, 4.0, 4.0)

        # 6. Draw Page Number Pill below thumbnail
        badge_text = str(page_idx + 1)
        font = QFont("Inter", 10, QFont.Weight.Medium if not is_selected else QFont.Weight.Bold)
        painter.setFont(font)

        badge_w = max(24.0, len(badge_text) * 7.5 + 14.0)
        badge_h = 17.0
        badge_x = r.left() + (r.width() - badge_w) / 2.0
        badge_y = pic_y + max_ph + 6.0
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        if is_selected:
            # Solid accent blue pill
            painter.setBrush(QBrush(QColor("#0a84ff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 8.5, 8.5)
            painter.setPen(QColor("#ffffff"))
        else:
            # Subtle pill under each thumbnail
            pill_bg = QColor(255, 255, 255, 20) if is_dark else QColor(0, 0, 0, 16)
            painter.setBrush(QBrush(pill_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 8.5, 8.5)
            painter.setPen(QColor("#98989d") if is_dark else QColor("#6e6e73"))

        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(140, 175)

class MacSidebar(QWidget):
    """Collapsible macOS sidebar (about 190px) providing Thumbnails, Contact Sheet, and Table of Contents."""
    
    page_selected = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macSidebar")
        self.setMinimumWidth(140)
        self.setMaximumWidth(450)
        
        self.document: Optional[Document] = None
        self.current_view_mode = "Thumbnails"
        self.thumbnail_width: int = 110
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar with small view dropdown
        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("sidebarHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(6)
        
        # Small Dropdown offering: Thumbnails, Contact Sheet, Table of Contents
        self.view_dropdown = QToolButton()
        self.view_dropdown.setObjectName("sidebarDropdown")
        self.view_dropdown.setText("Thumbnails")
        self.view_dropdown.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.view_dropdown.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.view_dropdown.setFixedHeight(26)
        self.view_dropdown.setIcon(MacIconFactory.create_icon("thumbnails", "#0a84ff", 14))

        self.view_menu = QMenu(self)
        self.view_menu.setObjectName("sidebarViewMenu")

        self.act_thumbs = QAction("Thumbnails", self)
        self.act_thumbs.triggered.connect(lambda: self.set_view_mode("Thumbnails"))
        self.view_menu.addAction(self.act_thumbs)

        self.act_contact = QAction("Contact Sheet", self)
        self.act_contact.triggered.connect(lambda: self.set_view_mode("Contact Sheet"))
        self.view_menu.addAction(self.act_contact)

        self.act_toc = QAction("Table of Contents", self)
        self.act_toc.triggered.connect(lambda: self.set_view_mode("Table of Contents"))
        self.view_menu.addAction(self.act_toc)

        self.view_dropdown.setMenu(self.view_menu)
        self.view_btn = self.view_dropdown  # Alias for compatibility
        header_layout.addWidget(self.view_dropdown)

        self.page_count_label = QLabel("")
        self.page_count_label.setStyleSheet("color: #8e8e93; font-size: 11px;")
        header_layout.addStretch()
        header_layout.addWidget(self.page_count_label)
        
        layout.addWidget(header)

        # Stacked view: 0: Thumbnails / Contact Sheet (ListWidget), 1: Outline/TOC (TreeWidget)
        self.stack = QStackedWidget()
        
        # 1. Thumbnails list
        self.thumb_list = QListWidget()
        self.thumb_list.setItemDelegate(MacThumbnailDelegate(self))
        self.thumb_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumb_list.currentRowChanged.connect(self._on_row_changed)
        self.thumb_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.thumb_list.customContextMenuRequested.connect(self._show_thumb_context_menu)
        self.thumb_list.installEventFilter(self)
        self.stack.addWidget(self.thumb_list)

        # 2. Outline / Table of contents tree
        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self._on_outline_item_clicked)
        self.stack.addWidget(self.outline_tree)

        layout.addWidget(self.stack)

        # Footer with Thumbnail Size Slider
        footer = QWidget()
        footer.setFixedHeight(28)
        footer.setObjectName("sidebarFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 2, 12, 2)
        footer_layout.setSpacing(6)

        lbl_s = QLabel()
        lbl_s.setPixmap(MacIconFactory.create_icon("thumbnails", "#8e8e93", 10).pixmap(10, 10))
        footer_layout.addWidget(lbl_s)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(70, 220)
        self.size_slider.setValue(110)
        self.size_slider.setToolTip("Thumbnail Size Slider")
        self.size_slider.setFixedHeight(16)
        self.size_slider.valueChanged.connect(self._on_thumbnail_size_changed)
        footer_layout.addWidget(self.size_slider)

        lbl_l = QLabel()
        lbl_l.setPixmap(MacIconFactory.create_icon("thumbnails", "#8e8e93", 16).pixmap(16, 16))
        footer_layout.addWidget(lbl_l)

        layout.addWidget(footer)

    def _on_thumbnail_size_changed(self, size: int):
        self.thumbnail_width = size
        item_w = size + 30
        item_h = int(size * 1.35) + 35
        for i in range(self.thumb_list.count()):
            it = self.thumb_list.item(i)
            if it:
                it.setSizeHint(QSize(item_w, item_h))
        self.thumb_list.update()

    def set_document(self, doc: Document):
        self.document = doc
        self.reload_thumbnails()
        self.reload_outline()

    def reload_thumbnails(self):
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        
        if not self.document:
            self.page_count_label.setText("")
            self.thumb_list.blockSignals(False)
            return

        self.page_count_label.setText(f"{self.document.page_count} Pages" if self.document.page_count > 1 else "1 Page")

        item_w = self.thumbnail_width + 30
        item_h = int(self.thumbnail_width * 1.35) + 35
        for idx in range(self.document.page_count):
            item = QListWidgetItem()
            item.setSizeHint(QSize(item_w, item_h))
            self.thumb_list.addItem(item)

        if self.document.page_count > 0:
            self.thumb_list.setCurrentRow(self.document.current_page)
        
        self.thumb_list.blockSignals(False)

    def reload_outline(self):
        self.outline_tree.clear()
        if not self.document:
            return
            
        outline = self.document.get_outline()
        # Keep view_dropdown ALWAYS enabled so users can toggle Thumbnails / Contact Sheet
        self.view_dropdown.setEnabled(True)
        if hasattr(self, "act_toc"):
            self.act_toc.setEnabled(bool(outline))

        if not outline:
            if self.stack.currentIndex() == 1:
                self.set_view_mode("Thumbnails")
            return

        self.view_btn.setEnabled(True)
        # Populate outline hierarchy
        parents = {0: self.outline_tree}
        for level, title, page_num in outline:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, page_num)
            parent = parents.get(level - 1, self.outline_tree)
            parent.addTopLevelItem(item) if parent is self.outline_tree else parent.addChild(item)
            parents[level] = item

    def select_page(self, page_idx: int):
        if 0 <= page_idx < self.thumb_list.count():
            self.thumb_list.blockSignals(True)
            self.thumb_list.setCurrentRow(page_idx)
            self.thumb_list.blockSignals(False)

    def _on_row_changed(self, row: int):
        if row >= 0:
            self.page_selected.emit(row)

    def _on_outline_item_clicked(self, item: QTreeWidgetItem, column: int):
        page_num = item.data(0, Qt.ItemDataRole.UserRole)
        if page_num is not None:
            self.page_selected.emit(page_num)

    def set_view_mode(self, mode_name: str):
        self.current_view_mode = mode_name
        self.view_dropdown.setText(mode_name)
        if mode_name == "Thumbnails":
            self.stack.setCurrentIndex(0)
            self.thumb_list.setViewMode(QListWidget.ViewMode.ListMode)
            self.thumb_list.setFlow(QListWidget.Flow.TopToBottom)
            self.thumb_list.setWrapping(False)
            self.thumb_list.setSpacing(4)
            self.view_dropdown.setIcon(MacIconFactory.create_icon("thumbnails", "#0a84ff", 14))
        elif mode_name == "Contact Sheet":
            self.stack.setCurrentIndex(0)
            self.thumb_list.setViewMode(QListWidget.ViewMode.IconMode)
            self.thumb_list.setFlow(QListWidget.Flow.LeftToRight)
            self.thumb_list.setWrapping(True)
            self.thumb_list.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.thumb_list.setSpacing(8)
            self.view_dropdown.setIcon(MacIconFactory.create_icon("thumbnails", "#0a84ff", 14))
        elif mode_name == "Table of Contents":
            self.stack.setCurrentIndex(1)
            self.view_dropdown.setIcon(MacIconFactory.create_icon("doc_proxy", "#0a84ff", 14))

    def _toggle_view_mode(self):
        if self.current_view_mode == "Thumbnails":
            self.set_view_mode("Table of Contents")
        else:
            self.set_view_mode("Thumbnails")

    def _show_thumb_context_menu(self, pos):
        if not self.document:
            return
        item = self.thumb_list.itemAt(pos)
        if not item:
            return
        idx = self.thumb_list.row(item)

        menu = QMenu(self)
        menu.setObjectName("thumbContextMenu")

        act_rot_cw = QAction("Rotate 90° Clockwise", self)
        act_rot_cw.triggered.connect(lambda: self.document.rotate_page(idx, 90))
        menu.addAction(act_rot_cw)

        act_rot_ccw = QAction("Rotate 90° Counter-Clockwise", self)
        act_rot_ccw.triggered.connect(lambda: self.document.rotate_page(idx, -90))
        menu.addAction(act_rot_ccw)

        menu.addSeparator()

        act_dup = QAction("Duplicate Page", self)
        act_dup.triggered.connect(lambda: self._duplicate_page(idx))
        menu.addAction(act_dup)

        act_insert = QAction("Insert Blank Page After", self)
        act_insert.triggered.connect(lambda: self._insert_blank_page(idx))
        menu.addAction(act_insert)

        menu.addSeparator()

        act_del = QAction("Delete Page", self)
        act_del.setShortcut("Delete")
        act_del.setEnabled(self.document.page_count > 1)
        act_del.triggered.connect(lambda: self._confirm_and_delete_page(idx))
        menu.addAction(act_del)

        menu.exec(self.thumb_list.mapToGlobal(pos))

    def _duplicate_page(self, idx: int):
        if self.document and self.document.duplicate_page(idx):
            self.reload_thumbnails()
            self.page_selected.emit(idx + 1)

    def _insert_blank_page(self, idx: int):
        if self.document and self.document.insert_blank_page(idx):
            self.reload_thumbnails()
            self.page_selected.emit(idx + 1)

    def _confirm_and_delete_page(self, idx: int):
        if not self.document:
            return
        if self.document.page_count <= 1:
            QMessageBox.information(self, "Delete Page", "Cannot delete the only page in the document.")
            return

        reply = QMessageBox.question(
            self, "Delete Page", 
            f"Are you sure you want to delete page {idx + 1}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.document.delete_page(idx)
            self.reload_thumbnails()

    def eventFilter(self, source, event):
        if source == self.thumb_list and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                row = self.thumb_list.currentRow()
                if row >= 0:
                    self._confirm_and_delete_page(row)
                    return True
        return super().eventFilter(source, event)
