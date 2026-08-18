"""High performance click-through transparent ghost overlay window for Waydroid gaming using PyQt6."""

from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QResizeEvent
from PyQt6.QtWidgets import QWidget
from typing import Dict, Optional, Callable

from vitouch.profile import GameProfile, KeyBinding
from vitouch.widgets.touch_button import TouchButtonWidget


class PlayOverlayWindow(QWidget):
    """Permanent 100% Transparent Ghost Overlay that is 100% Click-Through to Waydroid."""

    def __init__(
        self,
        profile: GameProfile,
        parent: Optional[QWidget] = None,
        *args,
        **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.profile = profile
        self.button_widgets: Dict[str, TouchButtonWidget] = {}

        # 1. Unbreakable Overlay Window Configuration (Override-Redirect + WindowTransparentForInput)
        self.setWindowTitle("ViTouch Play Overlay")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.resize(profile.resolution.width, profile.resolution.height)

        # 2. Render initial button widgets
        self.reload_profile(profile)

        # 3. Fast Periodic Always-on-Top Keeper
        self.ontop_timer = QTimer(self)
        self.ontop_timer.timeout.connect(self._keep_above)
        self.ontop_timer.start(250)

    def _keep_above(self) -> None:
        """Continuously ensure the overlay is layered strictly above Waydroid."""
        if not self.isVisible():
            return
        self.raise_()

    def reload_profile(self, profile: GameProfile) -> None:
        """Clear and recreate all TouchButtonWidgets with updated profile."""
        self.profile = profile
        for w in self.button_widgets.values():
            w.hide()
            w.deleteLater()
        self.button_widgets.clear()

        win_w = self.width() or self.profile.resolution.width
        win_h = self.height() or self.profile.resolution.height

        for binding in self.profile.bindings:
            widget = TouchButtonWidget(
                binding,
                False,
                self
            )
            self.button_widgets[binding.id] = widget

            center_x = int(round(binding.norm_x * win_w))
            center_y = int(round(binding.norm_y * win_h))
            px = center_x - (widget.width() // 2)
            py = center_y - (widget.height() // 2)
            widget.move(max(0, px), max(0, py))
            widget.show()

        self.show()
        self.raise_()
        self.update()

    def pulse_button(self, binding_id: str) -> None:
        """Flash active state when key is tapped and maintain top layer."""
        widget = self.button_widgets.get(binding_id)
        if widget and widget.isVisible():
            widget.trigger_activation_pulse()
        self.raise_()
        self.update()

    def paintEvent(self, event) -> None:
        """Play Mode is completely transparent."""
        pass
