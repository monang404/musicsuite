from PySide6.QtWidgets import QWidget, QPushButton, QSizePolicy, QLayout, QLayoutItem, QStyle
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize, QPropertyAnimation, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QCursor
from ui.themes.theme_manager import ThemeManager

class FlowLayout(QLayout):
    """
    A custom FlowLayout that automatically wraps items horizontally.
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self.item_list:
            wid = item.widget()
            space_x = spacing
            space_y = spacing
            
            if wid is not None:
                space_x += wid.style().pixelMetric(QStyle.PM_LayoutHorizontalSpacing)
                space_y += wid.style().pixelMetric(QStyle.PM_LayoutVerticalSpacing)
                
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class AnimatedChip(QPushButton):
    """
    A suggestion chip with soft QVariantAnimation hover and press states.
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self.bg_surface = ThemeManager.get_color("bg_surface")
        self.border = ThemeManager.get_color("border")
        self.border_hover = ThemeManager.get_color("border_hover")
        self.accent_border = ThemeManager.get_color("accent_border")
        self.text_secondary = ThemeManager.get_color("text_secondary")
        self.text_primary = ThemeManager.get_color("text_primary")
        self.accent_light = ThemeManager.get_color("accent_light")
        
        # Base style
        self.setStyleSheet(f"""
            QPushButton {{
                font-size: 13px;
                color: {self.text_secondary};
                background-color: {self.bg_surface};
                border: 1px solid {self.border};
                border-radius: 16px;
                padding: 8px 18px;
            }}
        """)
        
        # Animations
        self.border_anim = QVariantAnimation(self)
        self.border_anim.setDuration(200)
        self.border_anim.valueChanged.connect(self._update_color)
        
        # Convert hex strings to QColor for smooth interpolation
        self._current_border = QColor(self.border)
        self._current_text = QColor(self.text_secondary)
        self._current_bg = QColor(self.bg_surface)
        
        self.installEventFilter(self)

    def _update_color(self, val):
        border_col, text_col, bg_col = val
        self._current_border = border_col
        self._current_text = text_col
        self._current_bg = bg_col
        self.setStyleSheet(f"""
            QPushButton {{
                font-size: 13px;
                color: {text_col.name()};
                background-color: {bg_col.name()};
                border: 1px solid {border_col.name()};
                border-radius: 16px;
                padding: 8px 18px;
            }}
        """)

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == event.Type.Enter:
                self.border_anim.stop()
                self.border_anim.setStartValue([self._current_border, self._current_text, self._current_bg])
                self.border_anim.setEndValue([QColor(self.accent_border), QColor(self.text_primary), QColor(self.bg_surface)])
                self.border_anim.start()
            elif event.type() == event.Type.Leave:
                self.border_anim.stop()
                self.border_anim.setStartValue([self._current_border, self._current_text, self._current_bg])
                self.border_anim.setEndValue([QColor(self.border), QColor(self.text_secondary), QColor(self.bg_surface)])
                self.border_anim.start()
            elif event.type() == event.Type.MouseButtonPress:
                self.border_anim.stop()
                self._update_color([QColor(self.accent_border), QColor(self.text_primary), QColor(self.border_hover)])
            elif event.type() == event.Type.MouseButtonRelease:
                self._update_color([QColor(self.accent_border), QColor(self.text_primary), QColor(self.bg_surface)])
        return super().eventFilter(obj, event)


class ChipRow(QWidget):
    """
    A wrapping container for suggestion chips.
    Dynamically reflows as the window is resized.
    """
    chip_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = FlowLayout(self, margin=0, spacing=8)
        self._chips = []

    def set_suggestions(self, suggestions):
        self._clear_chips()
        
        for text in suggestions:
            btn = AnimatedChip(text)
            btn.clicked.connect(lambda checked, t=text: self.chip_clicked.emit(t))
            self.layout.addWidget(btn)
            self._chips.append(btn)
            
    def _clear_chips(self):
        for chip in self._chips:
            self.layout.removeWidget(chip)
            chip.deleteLater()
        self._chips.clear()
