"""
jarvis/actuation/actions.py
═══════════════════════════
OS-level actuation: app launching, URL opening, reminder scheduling,
window control, volume, screenshots, and clipboard.

Cross-platform support:
  - Windows:  subprocess + webbrowser + ctypes
  - macOS:    'open -a' / 'open' / osascript
  - Linux:    xdg-open / common binaries / pactl

Extensible app registry — add entries to APPS dict to teach Jarvis new targets.
Reminder engine uses threading.Timer (lightweight, no external deps).

PRD references: F003, F008
"""

import os
import platform
import re
import subprocess
import threading
import webbrowser
from datetime import datetime, timedelta


# ── Detect OS once ────────────────────────────────────────────────────────────
_OS = platform.system()    # "Windows" | "Darwin" | "Linux"


# ── App / URL registry ────────────────────────────────────────────────────────
# key           — substring to match from LLM [OPEN: ...] output
# (win, mac, linux, url)
#   win/mac/linux — list for subprocess.Popen (or None if not supported)
#   url           — string to open in browser (or None)

APPS = {
    # ── System apps ──────────────────────────────────────────────
    "notepad":       {"win": ["notepad.exe"],       "mac": ["open", "-a", "TextEdit"],   "linux": ["gedit"]},
    "calculator":    {"win": ["calc.exe"],           "mac": ["open", "-a", "Calculator"], "linux": ["gnome-calculator"]},
    "calc":          {"win": ["calc.exe"],           "mac": ["open", "-a", "Calculator"], "linux": ["gnome-calculator"]},
    "paint":         {"win": ["mspaint.exe"],        "mac": None,                         "linux": None},
    "task manager":  {"win": ["taskmgr.exe"],        "mac": ["open", "-a", "Activity Monitor"], "linux": ["gnome-system-monitor"]},
    "file explorer": {"win": ["explorer.exe"],       "mac": ["open", "."],                "linux": ["nautilus", "."]},
    "explorer":      {"win": ["explorer.exe"],       "mac": ["open", "."],                "linux": ["nautilus", "."]},
    "finder":        {"win": ["explorer.exe"],       "mac": ["open", "."],                "linux": ["nautilus", "."]},
    "cmd":           {"win": ["cmd.exe"],            "mac": ["open", "-a", "Terminal"],   "linux": ["gnome-terminal"]},
    "terminal":      {"win": ["cmd.exe"],            "mac": ["open", "-a", "Terminal"],   "linux": ["gnome-terminal"]},
    "powershell":    {"win": ["powershell.exe"],     "mac": None,                         "linux": None},
    "settings":      {"win": ["ms-settings:"],       "mac": ["open", "-a", "System Preferences"], "linux": ["gnome-control-center"]},
    "snipping tool": {"win": ["SnippingTool.exe"],   "mac": None,                         "linux": None},
    "clock":         {"win": ["ms-clock:"],          "mac": None,                         "linux": None},
    "photos":        {"win": ["ms-photos:"],         "mac": ["open", "-a", "Photos"],     "linux": None},

    # ── Dev tools ────────────────────────────────────────────────
    "vs code":       {"win": ["code"],               "mac": ["open", "-a", "Visual Studio Code"], "linux": ["code"]},
    "code":          {"win": ["code"],               "mac": ["open", "-a", "Visual Studio Code"], "linux": ["code"]},
    "pycharm":       {"win": ["pycharm"],            "mac": ["open", "-a", "PyCharm"],    "linux": ["pycharm"]},
    "postman":       {"win": ["postman"],            "mac": ["open", "-a", "Postman"],    "linux": ["postman"]},
    "sublime":       {"win": ["subl"],               "mac": ["open", "-a", "Sublime Text"], "linux": ["subl"]},
    "android studio":{"win": ["studio64.exe"],       "mac": ["open", "-a", "Android Studio"], "linux": ["studio"]},
    "intellij":      {"win": ["idea64.exe"],         "mac": ["open", "-a", "IntelliJ IDEA"], "linux": ["idea"]},

    # ── Communication ────────────────────────────────────────────
    "slack":         {"win": ["slack"],              "mac": ["open", "-a", "Slack"],      "linux": ["slack"]},
    "discord":       {"win": ["discord"],            "mac": ["open", "-a", "Discord"],    "linux": ["discord"]},
    "teams":         {"win": ["teams"],              "mac": ["open", "-a", "Microsoft Teams"], "linux": ["teams"]},
    "zoom":          {"win": ["zoom"],               "mac": ["open", "-a", "zoom.us"],    "linux": ["zoom"]},
    "whatsapp":      {"url": "https://web.whatsapp.com"},
    "telegram":      {"url": "https://web.telegram.org"},

    # ── Browsers / sites (URL-based, platform-agnostic) ─────────
    "browser":       {"url": "about:blank"},
    "youtube":       {"url": "https://youtube.com"},
    "instagram":     {"url": "https://instagram.com"},
    "github":        {"url": "https://github.com"},
    "gmail":         {"url": "https://mail.google.com"},
    "spotify":       {"url": "https://open.spotify.com"},
    "twitter":       {"url": "https://twitter.com"},
    "linkedin":      {"url": "https://linkedin.com"},
    "claude":        {"url": "https://claude.ai"},
    "chatgpt":       {"url": "https://chatgpt.com"},
    "google":        {"url": "https://google.com"},
    "reddit":        {"url": "https://reddit.com"},
    "stackoverflow": {"url": "https://stackoverflow.com"},
    "notion":        {"url": "https://notion.so"},
    "figma":         {"url": "https://figma.com"},
    "brave":         {"win": ["brave"],              "mac": ["open", "-a", "Brave Browser"], "linux": ["brave-browser"]},
    "edge":          {"win": ["msedge"],             "mac": ["open", "-a", "Microsoft Edge"], "linux": ["microsoft-edge"]},
    "chrome":        {"win": ["chrome"],             "mac": ["open", "-a", "Google Chrome"],  "linux": ["google-chrome"]},
    "firefox":       {"win": ["firefox"],            "mac": ["open", "-a", "Firefox"],        "linux": ["firefox"]},
}


class Actuator:
    """Executes parsed actions from the LLM brain."""

    def __init__(self, speak_fn):
        """
        speak_fn — callable(text: str) from voice/tts module.
        Injected to keep actuation decoupled from TTS.
        """
        self._speak = speak_fn
        self._reminders: list[threading.Timer] = []

    # ── App / URL launch ──────────────────────────────────────────────────────

    def open_app(self, app_name: str) -> bool:
        """
        Try to open an app or URL matching `app_name`.
        Returns True if a match was found and launched.
        """
        name = app_name.strip().lower()

        for key, entry in APPS.items():
            if key in name:
                try:
                    # URL-based entry (platform-agnostic)
                    if "url" in entry:
                        webbrowser.open(entry["url"])
                        self._speak(f"Opening {key}.")
                        return True

                    # Platform-specific binary
                    os_key = {"Windows": "win", "Darwin": "mac", "Linux": "linux"}.get(_OS)
                    cmd = entry.get(os_key) if os_key else None

                    if cmd:
                        subprocess.Popen(cmd, shell=(_OS == "Windows" and cmd[0].endswith(":")))
                        self._speak(f"Opening {key}.")
                        return True
                    else:
                        self._speak(f"Sorry, {key} isn't available on {_OS}.")
                        return True

                except FileNotFoundError:
                    self._speak(f"I couldn't find {key} on this system. Is it installed?")
                    return True
                except Exception as exc:
                    self._speak(f"Failed to open {key}: {exc}")
                    return True

        self._speak(f"I don't have {app_name!r} mapped yet. Want me to add it?")
        return True

    # ── Reminders ─────────────────────────────────────────────────────────────

    def set_reminder(self, time_str: str, message: str) -> bool:
        """
        Schedule a spoken reminder.
        time_str — "HH:MM" (24-hour) or relative like "5m", "10m"
        """
        delay_seconds = self._parse_time(time_str)
        if delay_seconds is None:
            self._speak(f"Sorry, I couldn't parse the time '{time_str}'.")
            return True

        def fire():
            self._speak(f"Reminder: {message}")

        t = threading.Timer(delay_seconds, fire)
        t.daemon = True
        t.start()
        self._reminders.append(t)

        # Confirm to user
        if delay_seconds < 120:
            eta = f"{int(delay_seconds)} seconds"
        else:
            eta = f"{int(delay_seconds // 60)} minutes"
        self._speak(f"Got it. I'll remind you in {eta}.")
        return True

    def cancel_all_reminders(self) -> None:
        for t in self._reminders:
            t.cancel()
        self._reminders.clear()

    # ── Window control ────────────────────────────────────────────────────────

    def minimize_window(self) -> None:
        """Minimize the active window."""
        if _OS == "Windows":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.user32.GetForegroundWindow(), 6  # SW_MINIMIZE
                )
                self._speak("Window minimized.")
            except Exception:
                self._speak("Couldn't minimize the window.")
        elif _OS == "Darwin":
            try:
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "m" using command down'],
                    check=True)
                self._speak("Window minimized.")
            except Exception:
                self._speak("Couldn't minimize the window.")
        else:
            try:
                subprocess.run(["xdotool", "windowminimize", "--sync",
                    subprocess.getoutput("xdotool getactivewindow")], check=True)
                self._speak("Window minimized.")
            except Exception:
                self._speak("Window control requires xdotool on Linux.")

    def maximize_window(self) -> None:
        """Maximize the active window."""
        if _OS == "Windows":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.user32.GetForegroundWindow(), 3  # SW_MAXIMIZE
                )
                self._speak("Window maximized.")
            except Exception:
                self._speak("Couldn't maximize the window.")
        elif _OS == "Darwin":
            try:
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "f" using {control down, command down}'],
                    check=True)
                self._speak("Window maximized.")
            except Exception:
                self._speak("Couldn't maximize the window.")
        else:
            try:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-b", "add,maximized_vert,maximized_horz"],
                    check=True)
                self._speak("Window maximized.")
            except Exception:
                self._speak("Window control requires wmctrl on Linux.")

    # ── Volume control ────────────────────────────────────────────────────────

    def volume_up(self) -> None:
        """Increase system volume by ~10%."""
        if _OS == "Windows":
            try:
                import ctypes
                # Simulate volume up key press
                VK_VOLUME_UP = 0xAF
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)  # key up
                self._speak("Volume up.")
            except Exception:
                self._speak("Couldn't adjust the volume.")
        elif _OS == "Darwin":
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)"])
            self._speak("Volume up.")
        else:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
            self._speak("Volume up.")

    def volume_down(self) -> None:
        """Decrease system volume by ~10%."""
        if _OS == "Windows":
            try:
                import ctypes
                VK_VOLUME_DOWN = 0xAE
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                self._speak("Volume down.")
            except Exception:
                self._speak("Couldn't adjust the volume.")
        elif _OS == "Darwin":
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10)"])
            self._speak("Volume down.")
        else:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
            self._speak("Volume down.")

    def volume_mute(self) -> None:
        """Toggle mute."""
        if _OS == "Windows":
            try:
                import ctypes
                VK_VOLUME_MUTE = 0xAD
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                self._speak("Mute toggled.")
            except Exception:
                self._speak("Couldn't toggle mute.")
        elif _OS == "Darwin":
            subprocess.run(["osascript", "-e", "set volume with output muted"])
            self._speak("Mute toggled.")
        else:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
            self._speak("Mute toggled.")

    # ── Screenshot ────────────────────────────────────────────────────────────

    def take_screenshot(self, save_dir: str = None) -> str | None:
        """
        Capture the screen and save to save_dir (default: Desktop).
        Returns the file path, or None on failure.
        """
        if save_dir is None:
            save_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"jarvis_screenshot_{timestamp}.png")

        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            self._speak(f"Screenshot saved to your Desktop.")
            return filepath
        except ImportError:
            self._speak("Screenshot requires Pillow. Run: pip install Pillow")
            return None
        except Exception as exc:
            self._speak(f"Screenshot failed: {exc}")
            return None

    # ── Lock screen ───────────────────────────────────────────────────────────

    def lock_screen(self) -> None:
        """Lock the workstation."""
        if _OS == "Windows":
            try:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                self._speak("Locking the workstation.")
            except Exception:
                self._speak("Couldn't lock the screen.")
        elif _OS == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"])
            self._speak("Locking the screen.")
        else:
            subprocess.run(["loginctl", "lock-session"])
            self._speak("Locking the screen.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_time(time_str: str) -> float | None:
        """
        Parse time_str into seconds from now.
        Supports: "HH:MM", "Xm" (X minutes), "Xs" (X seconds), "Xh" (X hours).
        """
        # Relative: "5m", "10m", "30s", "2h"
        m = re.match(r"^(\d+)\s*m(?:in(?:ute)?s?)?$", time_str.strip(), re.IGNORECASE)
        if m:
            return float(m.group(1)) * 60

        m = re.match(r"^(\d+)\s*s(?:ec(?:ond)?s?)?$", time_str.strip(), re.IGNORECASE)
        if m:
            return float(m.group(1))

        m = re.match(r"^(\d+)\s*h(?:(?:ou)?rs?)?$", time_str.strip(), re.IGNORECASE)
        if m:
            return float(m.group(1)) * 3600

        # Absolute: "15:30"
        m = re.match(r"^(\d{1,2}):(\d{2})$", time_str.strip())
        if m:
            now    = datetime.now()
            target = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
            if target <= now:
                target += timedelta(days=1)   # Next occurrence
            return (target - now).total_seconds()

        return None