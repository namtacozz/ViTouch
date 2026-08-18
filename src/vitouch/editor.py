"""PyQt6 Editor Overlay Window and Toolbar for ViTouch."""

from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QResizeEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QInputDialog,
    QFrame
)
from typing import Optional, Callable, Dict, List

from vitouch.profile import (
    GameProfile,
    KeyBinding,
    list_available_profiles,
    create_new_custom_profile,
    load_profile_by_name,
)
from vitouch.widgets.touch_button import TouchButtonWidget


QT_KEY_TO_EVDEV = {
    Qt.Key.Key_A: ("KEY_A", "A"),
    Qt.Key.Key_B: ("KEY_B", "B"),
    Qt.Key.Key_C: ("KEY_C", "C"),
    Qt.Key.Key_D: ("KEY_D", "D"),
    Qt.Key.Key_E: ("KEY_E", "E"),
    Qt.Key.Key_F: ("KEY_F", "F"),
    Qt.Key.Key_G: ("KEY_G", "G"),
    Qt.Key.Key_H: ("KEY_H", "H"),
    Qt.Key.Key_I: ("KEY_I", "I"),
    Qt.Key.Key_J: ("KEY_J", "J"),
    Qt.Key.Key_K: ("KEY_K", "K"),
    Qt.Key.Key_L: ("KEY_L", "L"),
    Qt.Key.Key_M: ("KEY_M", "M"),
    Qt.Key.Key_N: ("KEY_N", "N"),
    Qt.Key.Key_O: ("KEY_O", "O"),
    Qt.Key.Key_P: ("KEY_P", "P"),
    Qt.Key.Key_Q: ("KEY_Q", "Q"),
    Qt.Key.Key_R: ("KEY_R", "R"),
    Qt.Key.Key_S: ("KEY_S", "S"),
    Qt.Key.Key_T: ("KEY_T", "T"),
    Qt.Key.Key_U: ("KEY_U", "U"),
    Qt.Key.Key_V: ("KEY_V", "V"),
    Qt.Key.Key_W: ("KEY_W", "W"),
    Qt.Key.Key_X: ("KEY_X", "X"),
    Qt.Key.Key_Y: ("KEY_Y", "Y"),
    Qt.Key.Key_Z: ("KEY_Z", "Z"),
    Qt.Key.Key_0: ("KEY_0", "0"),
    Qt.Key.Key_1: ("KEY_1", "1"),
    Qt.Key.Key_2: ("KEY_2", "2"),
    Qt.Key.Key_3: ("KEY_3", "3"),
    Qt.Key.Key_4: ("KEY_4", "4"),
    Qt.Key.Key_5: ("KEY_5", "5"),
    Qt.Key.Key_6: ("KEY_6", "6"),
    Qt.Key.Key_7: ("KEY_7", "7"),
    Qt.Key.Key_8: ("KEY_8", "8"),
    Qt.Key.Key_9: ("KEY_9", "9"),
    Qt.Key.Key_Space: ("KEY_SPACE", "SPC"),
    Qt.Key.Key_Tab: ("KEY_TAB", "TAB"),
    Qt.Key.Key_Return: ("KEY_ENTER", "ENT"),
    Qt.Key.Key_Enter: ("KEY_ENTER", "ENT"),
    Qt.Key.Key_Escape: ("KEY_ESC", "ESC"),
    Qt.Key.Key_Shift: ("KEY_LEFTSHIFT", "SFT"),
    Qt.Key.Key_Control: ("KEY_LEFTCTRL", "CTL"),
    Qt.Key.Key_Alt: ("KEY_LEFTALT", "ALT"),
    Qt.Key.Key_Backspace: ("KEY_BACKSPACE", "BKSP"),
}


def qt_key_to_evdev(event: QKeyEvent) -> tuple[str, str]:
    """Convert Qt key event to evdev code and display string."""
    qt_key = event.key()
    if qt_key in QT_KEY_TO_EVDEV:
        return QT_KEY_TO_EVDEV[qt_key]
    txt = event.text().upper()
    if txt and txt.isalnum():
        return f"KEY_{txt}", txt
    return f"KEY_{qt_key}", "?"


class EditToolbar(QFrame):
    """Spacious Floating HUD toolbar displayed in Edit Mode with Profile Management, Hold Duration, and Quit button."""

    def __init__(
        self,
        active_profile_name: str,
        initial_duration_ms: int,
        on_profile_selected: Callable[[str], None],
        on_add_binding: Callable[[], None],
        on_duration_changed: Callable[[int], None],
        on_save_profile: Callable[[], None],
        on_exit_edit: Callable[[], None],
        on_quit_app: Callable[[], None],
        parent: Optional[QWidget] = None,
        *args,
        **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.on_profile_selected = on_profile_selected
        self.on_duration_changed = on_duration_changed

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.98);
                border: 1.5px solid rgba(255, 255, 255, 0.3);
                border-radius: 14px;
            }
            QLabel#title {
                color: #38BDF8;
                font-weight: 900;
                font-size: 15px;
                padding: 6px 14px;
                background: rgba(56, 189, 248, 0.18);
                border: 1px solid rgba(56, 189, 248, 0.45);
                border-radius: 8px;
            }
            QLabel#lbl_dur {
                color: #94A3B8;
                font-weight: bold;
                font-size: 12px;
                padding-left: 4px;
            }
            QSpinBox {
                background-color: #1E293B;
                color: #38BDF8;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 5px 8px;
                min-width: 85px;
            }
            QSpinBox:hover {
                border-color: #38BDF8;
            }
            QComboBox {
                background-color: #1E293B;
                color: #F8FAFC;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #38BDF8;
            }
            QComboBox QAbstractItemView {
                background-color: #0F172A;
                color: #FFFFFF;
                selection-background-color: #2563EB;
                border: 1px solid #334155;
            }
            QPushButton {
                background-color: rgba(30, 41, 59, 0.95);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 1.0);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton#btn_save {
                background-color: #2563EB;
                border-color: #60A5FA;
            }
            QPushButton#btn_save:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btn_play {
                background-color: #059669;
                border-color: #34D399;
            }
            QPushButton#btn_play:hover {
                background-color: #047857;
            }
            QPushButton#btn_quit {
                background-color: #DC2626;
                border-color: #F87171;
            }
            QPushButton#btn_quit:hover {
                background-color: #B91C1C;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # 1. Title
        lbl_title = QLabel("🏷 ViTouch", self)
        lbl_title.setObjectName("title")
        layout.addWidget(lbl_title)

        # 2. Profile Dropdown
        self.combo_profiles = QComboBox(self)
        self.refresh_profiles_list(active_profile_name)
        self.combo_profiles.currentTextChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo_profiles)

        # 3. New Profile button
        btn_new_prof = QPushButton("➕ Mới", self)
        btn_new_prof.clicked.connect(self._on_new_profile_clicked)
        layout.addWidget(btn_new_prof)

        # 4. Add Key button
        btn_add = QPushButton("➕ Thêm Phím", self)
        btn_add.clicked.connect(on_add_binding)
        layout.addWidget(btn_add)

        # 5. Touch Duration SpinBox
        lbl_dur = QLabel("⏱ Giữ:", self)
        lbl_dur.setObjectName("lbl_dur")
        layout.addWidget(lbl_dur)

        self.spin_duration = QSpinBox(self)
        self.spin_duration.setRange(20, 500)
        self.spin_duration.setSingleStep(10)
        self.spin_duration.setSuffix(" ms")
        self.spin_duration.setValue(max(20, initial_duration_ms or 120))
        self.spin_duration.valueChanged.connect(self._on_spin_changed)
        layout.addWidget(self.spin_duration)

        # 6. Save Button
        btn_save = QPushButton("💾 Lưu", self)
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(on_save_profile)
        layout.addWidget(btn_save)

        # 7. Play Mode Button
        btn_play = QPushButton("▶ Chơi (F2)", self)
        btn_play.setObjectName("btn_play")
        btn_play.clicked.connect(on_exit_edit)
        layout.addWidget(btn_play)

        # 8. Quit ViTouch Button (Far Right)
        btn_quit = QPushButton("✕ Thoát", self)
        btn_quit.setObjectName("btn_quit")
        btn_quit.clicked.connect(on_quit_app)
        layout.addWidget(btn_quit)

    def _on_spin_changed(self, val: int) -> None:
        if self.on_duration_changed:
            self.on_duration_changed(val)

    def refresh_profiles_list(self, active_name: str) -> None:
        """Refresh the profile list in the dropdown."""
        self.combo_profiles.blockSignals(True)
        self.combo_profiles.clear()
        profiles = list_available_profiles()
        for p in profiles:
            self.combo_profiles.addItem(p)

        safe_active = active_name.lower().replace(" ", "_")
        idx = self.combo_profiles.findText(safe_active)
        if idx >= 0:
            self.combo_profiles.setCurrentIndex(idx)
        self.combo_profiles.blockSignals(False)

    def _on_combo_changed(self, profile_name: str) -> None:
        if profile_name and self.on_profile_selected:
            self.on_profile_selected(profile_name)

    def _on_new_profile_clicked(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Tạo Profile Game Mới",
            "Nhập tên profile game mới (vd: wild_rift, genshin, pubg):"
        )
        if ok and name.strip():
            safe_name = name.strip().lower().replace(" ", "_")
            create_new_custom_profile(safe_name)
            self.refresh_profiles_list(safe_name)
            if self.on_profile_selected:
                self.on_profile_selected(safe_name)


class EditorOverlayWindow(QWidget):
    """Full-screen interactive editor overlay where mouse is fully captured for editing."""

    profile_saved = pyqtSignal(object)
    profile_switched = pyqtSignal(object)
    mode_switched_to_play = pyqtSignal()
    app_quit_requested = pyqtSignal()

    def __init__(self, profile: GameProfile, parent: Optional[QWidget] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.profile = profile
        self.button_widgets: Dict[str, TouchButtonWidget] = {}
        self.rebinding_binding: Optional[KeyBinding] = None

        self.setWindowTitle("ViTouch Editor")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.resize(profile.resolution.width, profile.resolution.height)

        # Spacious HUD Toolbar with Profile, Touch Duration, and Quit button
        safe_name = profile.name.lower().replace(" ", "_")
        self.editor_toolbar = EditToolbar(
            active_profile_name=safe_name,
            initial_duration_ms=profile.tap_duration_ms,
            on_profile_selected=self._on_profile_selected,
            on_add_binding=self._on_add_binding_clicked,
            on_duration_changed=self._on_duration_changed,
            on_save_profile=self._on_save_profile_clicked,
            on_exit_edit=lambda: self.mode_switched_to_play.emit(),
            on_quit_app=lambda: self.app_quit_requested.emit(),
            parent=self
        )

        self._rebuild_buttons()

    def _on_duration_changed(self, val: int) -> None:
        self.profile.tap_duration_ms = val
        self.profile_saved.emit(self.profile)

    def load_profile(self, profile: GameProfile) -> None:
        """Load new profile and refresh widgets."""
        self.profile = profile
        self._cancel_rebinding()
        self.editor_toolbar.refresh_profiles_list(profile.name)
        self.editor_toolbar.spin_duration.blockSignals(True)
        self.editor_toolbar.spin_duration.setValue(profile.tap_duration_ms or 120)
        self.editor_toolbar.spin_duration.blockSignals(False)
        self._rebuild_buttons()
        self.update()

    def _on_profile_selected(self, profile_name: str) -> None:
        prof = load_profile_by_name(profile_name)
        self.load_profile(prof)
        self.profile_switched.emit(prof)

    def _rebuild_buttons(self) -> None:
        for w in self.button_widgets.values():
            w.hide()
            w.deleteLater()
        self.button_widgets.clear()

        win_w = self.width() or self.profile.resolution.width
        win_h = self.height() or self.profile.resolution.height

        for binding in self.profile.bindings:
            widget = TouchButtonWidget(
                binding,
                True,
                self
            )
            widget.clicked.connect(self._start_rebinding)
            widget.double_clicked.connect(self._start_rebinding)
            widget.deleted.connect(self._delete_binding)
            self.button_widgets[binding.id] = widget

            center_x = int(round(binding.norm_x * win_w))
            center_y = int(round(binding.norm_y * win_h))
            px = center_x - (widget.width() // 2)
            py = center_y - (widget.height() // 2)
            widget.move(max(0, px), max(0, py))
            widget.show()

    def _start_rebinding(self, binding: KeyBinding) -> None:
        self._cancel_rebinding()
        self.rebinding_binding = binding
        widget = self.button_widgets.get(binding.id)
        if widget:
            widget.set_rebinding(True)
        self.setFocus()

    def _cancel_rebinding(self) -> None:
        if self.rebinding_binding:
            widget = self.button_widgets.get(self.rebinding_binding.id)
            if widget:
                widget.set_rebinding(False)
            self.rebinding_binding = None

    def handle_rebind_key(self, evdev_key: str, display_key: str) -> bool:
        if not self.rebinding_binding:
            return False

        b = self.rebinding_binding
        b.key = evdev_key
        b.display_key = display_key

        widget = self.button_widgets.get(b.id)
        if widget:
            widget.set_rebinding(False)

        self.rebinding_binding = None
        self._on_save_profile_clicked()
        self.update()
        return True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.rebinding_binding:
            evdev_name, disp_char = qt_key_to_evdev(event)
            self.handle_rebind_key(evdev_name, disp_char)
            event.accept()
            return
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win_w = self.width() or self.profile.resolution.width
            win_h = self.height() or self.profile.resolution.height
            pos = event.position().toPoint()

            norm_x = max(0.0, min(1.0, pos.x() / win_w))
            norm_y = max(0.0, min(1.0, pos.y() / win_h))

            new_id = f"btn_custom_{len(self.profile.bindings) + 1}"
            new_binding = KeyBinding(
                id=new_id,
                key="KEY_F",
                display_key="F",
                norm_x=norm_x,
                norm_y=norm_y,
                color="#E2E8F0"
            )
            self.profile.bindings.append(new_binding)
            self._rebuild_buttons()
            self._start_rebinding(new_binding)

    def _delete_binding(self, binding: KeyBinding) -> None:
        if self.rebinding_binding and self.rebinding_binding.id == binding.id:
            self._cancel_rebinding()
        self.profile.bindings = [b for b in self.profile.bindings if b.id != binding.id]
        self._rebuild_buttons()

    def _on_add_binding_clicked(self) -> None:
        new_id = f"btn_custom_{len(self.profile.bindings) + 1}"
        new_binding = KeyBinding(
            id=new_id,
            key="KEY_F",
            display_key="F",
            norm_x=0.5,
            norm_y=0.5,
            color="#E2E8F0"
        )
        self.profile.bindings.append(new_binding)
        self._rebuild_buttons()
        self._start_rebinding(new_binding)

    def _on_save_profile_clicked(self) -> None:
        self.profile_saved.emit(self.profile)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_toolbar()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._position_toolbar()
        self.raise_()

    def _position_toolbar(self) -> None:
        tb_w = min(1180, max(850, self.width() - 20))
        self.editor_toolbar.resize(tb_w, 54)
        self.editor_toolbar.move(max(0, (self.width() - tb_w) // 2), 14)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(QColor(15, 23, 42, 110)))
