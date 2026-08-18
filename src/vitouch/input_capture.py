"""Global keyboard input capture via Linux evdev subsystem."""

import glob
import os
import select
import threading
import time
from typing import Callable, Dict, List, Optional, Set

try:
    import evdev
    from evdev import InputDevice, ecodes as e
    HAVE_EVDEV = True
except ImportError:
    HAVE_EVDEV = False


class InputCapture:
    """Monitors raw Linux input devices for keyboard events without grabbing."""

    def __init__(self, target_device_path: Optional[str] = None):
        self.target_device_path = target_device_path
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._devices: List[InputDevice] = []
        self._pressed_keys: Set[str] = set()

        # Callbacks: on_key_down(key_name: str), on_key_up(key_name: str)
        self.on_key_down: Optional[Callable[[str], None]] = None
        self.on_key_up: Optional[Callable[[str], None]] = None

    @staticmethod
    def find_keyboard_devices() -> List[str]:
        """Scan /dev/input/event* and find devices that have keyboard keys."""
        if not HAVE_EVDEV:
            return []

        kb_paths = []
        for path in sorted(glob.glob("/dev/input/event*")):
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if e.EV_KEY in caps:
                    keys = caps[e.EV_KEY]
                    # Check if device has basic alphanumeric keys (e.g. KEY_A, KEY_SPACE, KEY_ENTER)
                    if (e.KEY_A in keys or e.KEY_Q in keys) and e.KEY_SPACE in keys:
                        kb_paths.append(path)
            except (PermissionError, OSError):
                pass
        return kb_paths

    def start(self) -> bool:
        """Start listening for keyboard events in a background thread."""
        if not HAVE_EVDEV:
            print("[InputCapture] evdev not available.")
            return False

        if self._running:
            return True

        self._devices = []
        device_paths = [self.target_device_path] if self.target_device_path else self.find_keyboard_devices()

        for path in device_paths:
            if path and os.path.exists(path):
                try:
                    dev = InputDevice(path)
                    self._devices.append(dev)
                    print(f"[InputCapture] Monitoring keyboard: {dev.name} ({path})")
                except PermissionError:
                    print(f"[InputCapture] Permission denied for {path}. Add user to 'input' group.")
                except Exception as ex:
                    print(f"[InputCapture] Could not open {path}: {ex}")

        if not self._devices:
            print("[InputCapture] No accessible keyboard devices found in /dev/input/.")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ViTouch-InputCapture")
        self._thread.start()
        return True

    def _run_loop(self) -> None:
        """Main event polling loop."""
        while self._running:
            try:
                # Use select on active device file descriptors
                valid_devices = [d for d in self._devices if d.fd is not None]
                if not valid_devices:
                    time.sleep(1.0)
                    continue

                r, _, _ = select.select(valid_devices, [], [], 0.2)
                for dev in r:
                    try:
                        for event in dev.read():
                            if event.type == e.EV_KEY:
                                self._handle_key_event(event)
                    except (OSError, IOError):
                        # Device disconnected or errored
                        pass
            except Exception as ex:
                if self._running:
                    time.sleep(0.5)

    def _handle_key_event(self, event) -> None:
        """Process an EV_KEY event (0=release, 1=press, 2=hold)."""
        key_code = event.code
        # Lookup key name from ecodes
        key_name = e.KEY.get(key_code)
        if isinstance(key_name, list):
            key_name = key_name[0]
        if not key_name:
            key_name = f"KEY_{key_code}"

        val = event.value
        if val == 1:  # Key press
            self._pressed_keys.add(key_name)
            if self.on_key_down:
                try:
                    self.on_key_down(key_name)
                except Exception as ex:
                    print(f"[InputCapture] Error in on_key_down callback: {ex}")
        elif val == 0:  # Key release
            self._pressed_keys.discard(key_name)
            if self.on_key_up:
                try:
                    self.on_key_up(key_name)
                except Exception as ex:
                    print(f"[InputCapture] Error in on_key_up callback: {ex}")

    def is_key_pressed(self, key_name: str) -> bool:
        """Check if a specific key is currently held down."""
        return key_name in self._pressed_keys

    def stop(self) -> None:
        """Stop capturing input and close device handles."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass
        self._devices.clear()
        self._pressed_keys.clear()
