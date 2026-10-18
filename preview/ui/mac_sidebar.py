"""
macOS style collapsible left sidebar with page thumbnails and table of contents outline.
Features a custom thumbnail delegate replicating Apple Preview's page cards & badges.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QTreeWidget, QTreeWidgetItem, QLabel, QStackedWidget, QToolButton,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle, QMenu
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QModelIndex

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
        pix = doc.get_thumbnail(page_idx, width=110)
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
        max_pw, max_ph = 110.0, 130.0
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

        act_thumbs = QAction("Thumbnails", self)
        act_thumbs.triggered.connect(lambda: self.set_view_mode("Thumbnails"))
        self.view_menu.addAction(act_thumbs)

        act_contact = QAction("Contact Sheet", self)
        act_contact.triggered.connect(lambda: self.set_view_mode("Contact Sheet"))
        self.view_menu.addAction(act_contact)

        act_toc = QAction("Table of Contents", self)
        act_toc.triggered.connect(lambda: self.set_view_mode("Table of Contents"))
        self.view_menu.addAction(act_toc)

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
        self.stack.addWidget(self.thumb_list)

        # 2. Outline / Table of contents tree
        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self._on_outline_item_clicked)
        self.stack.addWidget(self.outline_tree)

        layout.addWidget(self.stack)

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

        for idx in range(self.document.page_count):
            item = QListWidgetItem()
            item.setSizeHint(QSize(140, 175))
            self.thumb_list.addItem(item)

        if self.document.page_count > 0:
            self.thumb_list.setCurrentRow(self.document.current_page)
        
        self.thumb_list.blockSignals(False)

    def reload_outline(self):
        self.outline_tree.clear()
        if not self.document:
            return
            
        outline = self.document.get_outline()
        if not outline:
            self.view_btn.setEnabled(False)
            self.stack.setCurrentIndex(0)
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
