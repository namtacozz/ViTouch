"""PyQt6 Translucent Frosted Glass Touch Button Widget with In-Place Quick Rebind and Hover Delete Badge."""

from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import QWidget
from typing import Optional

from vitouch.profile import KeyBinding


class TouchButtonWidget(QWidget):
    """Clean circular translucent touch button without distracting labels."""

    clicked = pyqtSignal(object)       # Emits binding when clicked in edit mode
    double_clicked = pyqtSignal(object)# Emits binding when double-clicked to rebind
    moved = pyqtSignal(object)         # Emits binding when moved
    deleted = pyqtSignal(object)       # Emits binding when delete 'X' is clicked

    def __init__(
        self,
        binding: KeyBinding,
        is_edit_mode: bool = False,
        parent: Optional[QWidget] = None,
        *args,
        **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.binding = binding
        self.is_edit_mode = is_edit_mode
        self.is_hovered = False
        self.is_active_pulse = False
        self.is_rebinding = False

        # Drag tracking
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._drag_start_widget_pos = QPoint()

        # Dimensions: Circular button size
        self.circle_radius = max(24, binding.radius)
        self.circle_diam = self.circle_radius * 2
        self.widget_size = self.circle_diam + 12

        self.resize(self.widget_size, self.widget_size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

    def set_edit_mode(self, edit_mode: bool) -> None:
        self.is_edit_mode = edit_mode
        if not edit_mode:
            self.is_rebinding = False
        self.setCursor(Qt.CursorShape.PointingHandCursor if edit_mode else Qt.CursorShape.ArrowCursor)
        self.update()

    def set_rebinding(self, rebinding: bool) -> None:
        self.is_rebinding = rebinding
        self.update()

    def trigger_activation_pulse(self) -> None:
        """Flash active amber glow for 140ms when key is pressed."""
        self.is_active_pulse = True
        self.update()
        QTimer.singleShot(140, self._end_pulse)

    def _end_pulse(self) -> None:
        self.is_active_pulse = False
        self.update()

    def enterEvent(self, event) -> None:
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if not self.is_edit_mode:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked on delete 'X' badge (top-right corner)
            del_rect = self._get_delete_badge_rect()
            if del_rect.contains(event.position().toPoint()):
                self.deleted.emit(self.binding)
                return

            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_start_widget_pos = self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if not self.is_edit_mode:
            super().mouseMoveEvent(event)
            return

        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            parent = self.parentWidget()
            if parent:
                parent_w = parent.width() or 1366
                parent_h = parent.height() or 768
                new_x = max(0, min(parent_w - self.width(), self._drag_start_widget_pos.x() + delta.x()))
                new_y = max(0, min(parent_h - self.height(), self._drag_start_widget_pos.y() + delta.y()))
                self.move(new_x, new_y)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if not self.is_edit_mode:
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.CursorShape.PointingHandCursor)

                # Check if it was a simple click (minimal movement)
                delta = event.globalPosition().toPoint() - self._drag_start_pos
                if abs(delta.x()) < 4 and abs(delta.y()) < 4:
                    self.clicked.emit(self.binding)
                else:
                    # Update normalized coordinates
                    parent = self.parentWidget()
                    if parent:
                        parent_w = parent.width() or 1366
                        parent_h = parent.height() or 768
                        center_x = self.x() + (self.width() / 2.0)
                        center_y = self.y() + (self.height() / 2.0)
                        self.binding.norm_x = max(0.0, min(1.0, center_x / parent_w))
                        self.binding.norm_y = max(0.0, min(1.0, center_y / parent_h))
                        self.moved.emit(self.binding)

    def mouseDoubleClickEvent(self, event) -> None:
        if self.is_edit_mode and event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.binding)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _get_delete_badge_rect(self) -> QRect:
        """Get bounding rect of tiny delete 'X' button at top-right."""
        cx = self.width() - 8
        cy = 8
        return QRect(cx - 7, cy - 7, 14, 14)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Circle center
        cx = float(self.width() / 2.0)
        cy = float(self.height() / 2.0)
        radius = float(self.circle_radius)

        circle_path = QPainterPath()
        circle_path.addEllipse(QPointF(cx, cy), radius, radius)

        if self.is_active_pulse:
            # Bright amber pulse on key press
            painter.fillPath(circle_path, QBrush(QColor(245, 158, 11, 230)))
            pulse_pen = QPen(QColor(254, 240, 138), 3)
            painter.strokePath(circle_path, pulse_pen)
        elif self.is_rebinding:
            # Active Quick Rebind Mode: glowing gold dashed outline
            painter.fillPath(circle_path, QBrush(QColor(245, 158, 11, 80)))
            rebind_pen = QPen(QColor(251, 191, 36, 255), 2.5, Qt.PenStyle.DashLine)
            painter.strokePath(circle_path, rebind_pen)
        else:
            # Subtle translucent light-gray frosted glass
            dark_backing = QColor(15, 23, 42, 95)
            translucent_gray = QColor(226, 232, 240, 48)
            painter.fillPath(circle_path, QBrush(dark_backing))
            painter.fillPath(circle_path, QBrush(translucent_gray))

            if self.is_edit_mode:
                pen = QPen(QColor(56, 189, 248, 220), 1.8, Qt.PenStyle.DashLine)
            else:
                pen = QPen(QColor(255, 255, 255, 120), 1.5)
            painter.strokePath(circle_path, pen)

        # Draw Centered Key Character (Bold, Crisp White with Dark Shadow)
        painter.setFont(QFont("Arial", 14, QFont.Weight.Black))
        key_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        disp_text = "..." if self.is_rebinding else self.binding.display_key

        # Shadow
        painter.setPen(QColor(0, 0, 0, 240))
        painter.drawText(key_rect.translated(1, 1), Qt.AlignmentFlag.AlignCenter, disp_text)
        # Foreground
        if self.is_rebinding:
            painter.setPen(QColor(251, 191, 36, 255))
        else:
            painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(key_rect, Qt.AlignmentFlag.AlignCenter, disp_text)

        # Tiny Delete 'X' Badge (Only visible in Edit Mode on hover)
        if self.is_edit_mode and self.is_hovered:
            del_rect = self._get_delete_badge_rect()
            del_path = QPainterPath()
            del_path.addEllipse(QRectF(del_rect))

            painter.fillPath(del_path, QBrush(QColor(239, 68, 68, 240)))
            del_pen = QPen(QColor(255, 255, 255, 255), 1)
            painter.strokePath(del_path, del_pen)

            painter.setFont(QFont("Arial", 8, QFont.Weight.Black))
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(QRectF(del_rect), Qt.AlignmentFlag.AlignCenter, "✕")
