"""
jarvis/vision/camera.py
════════════════════════
Computer Vision module — M3 implementation.

Capabilities (PRD F004):
  • Live webcam feed capture
  • Object detection via Tiny YOLOv8
  • Image captioning via CLIP / BLIP
  • QR code / barcode scanning
  • Screenshot analysis (read what's on screen)
  • Document scanning
  • Frame-to-base64 for HUD streaming

Optional dependencies:
  pip install opencv-python ultralytics transformers pillow pyzbar

Set VISION_ENABLED = True in config.py to activate.

PRD references: F004, M3
"""

import base64
import platform

_CV2_AVAILABLE = False
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    pass


class VisionEngine:
    """
    Computer vision engine with webcam capture and model inference.

    Usage
    ─────
        vision = VisionEngine()
        vision.start_capture()

        # Get current frame description
        caption = vision.describe_scene()
        # → "A person sitting at a desk with two monitors"

        # Detect objects
        objects = vision.detect_objects()
        # → [{"label": "person", "confidence": 0.92, "box": [x,y,w,h]}]

        # Scan QR code
        data = vision.scan_qr()
        # → "https://example.com"

        vision.stop_capture()
    """

    def __init__(self, camera_index: int = 0):
        self._camera_index = camera_index
        self._cap = None
        self._yolo = None
        self._clip = None

    # ── Capture ───────────────────────────────────────────────────────────────

    def start_capture(self) -> bool:
        """Start webcam capture. Returns True if successful."""
        if not _CV2_AVAILABLE:
            print("  [VISION] OpenCV not installed. Run: pip install opencv-python")
            return False

        self._cap = cv2.VideoCapture(self._camera_index)
        if not self._cap.isOpened():
            print("  [VISION] Failed to open camera.")
            return False

        print(f"  📷  Camera {self._camera_index} active.")
        return True

    def stop_capture(self) -> None:
        """Release webcam."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            print("  📷  Camera released.")

    def is_active(self) -> bool:
        """Check if camera is currently active."""
        return self._cap is not None and self._cap.isOpened()

    def get_frame(self):
        """Capture a single frame. Returns numpy array or None."""
        if self._cap is None or not self._cap.isOpened():
            return None
        ret, frame = self._cap.read()
        return frame if ret else None

    # ── High-level API (used by main.py) ──────────────────────────────────────

    def describe_what_you_see(self) -> str:
        """
        All-in-one: capture frame → detect objects + caption.
        Returns a human-readable description of the current scene.
        
        This is the method called when the user says "what do you see?"
        """
        frame = self.get_frame()
        if frame is None:
            return "I don't have camera access right now. Enable it in config.py."

        parts = []

        # Try object detection first (fast)
        objects = self.detect_objects(frame)
        if objects:
            labels = list(set(o["label"] for o in objects))
            if len(labels) == 1:
                parts.append(f"I can see a {labels[0]}")
            else:
                items = ", ".join(labels[:-1]) + f" and {labels[-1]}"
                parts.append(f"I can see {items}")

        # Try scene captioning (slower, richer)
        caption = self.describe_scene(frame)
        if caption and not caption.startswith("["):
            parts.append(caption)

        if not parts:
            return "I can see the camera feed but couldn't identify anything specific."

        return ". ".join(parts) + "."

    # ── Frame to base64 (for HUD streaming) ───────────────────────────────────

    def frame_to_base64(self, frame=None, quality: int = 50) -> str | None:
        """
        Convert a frame to a base64-encoded JPEG string.
        Useful for sending preview frames to the HUD via WebSocket.
        
        Returns base64 string or None if no frame.
        """
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return None

        if not _CV2_AVAILABLE:
            return None

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return base64.b64encode(buffer).decode('utf-8')

    # ── Object Detection (YOLO) ───────────────────────────────────────────────

    def detect_objects(self, frame=None):
        """
        Run object detection on a frame (or capture one).
        Returns list of {"label": str, "confidence": float, "box": [x,y,w,h]}.

        Requires: pip install ultralytics
        """
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return []

        # Lazy-load YOLO
        if self._yolo is None:
            try:
                from ultralytics import YOLO
                self._yolo = YOLO("yolov8n.pt")   # Nano model, ~6MB
                print("  [VISION] YOLOv8 nano loaded.")
            except ImportError:
                print("  [VISION] ultralytics not installed. Run: pip install ultralytics")
                return []
            except Exception as exc:
                print(f"  [VISION] YOLO load failed: {exc}")
                return []

        try:
            results = self._yolo(frame, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    detections.append({
                        "label": r.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "box": box.xywh[0].tolist(),
                    })
            return detections
        except Exception as exc:
            print(f"  [VISION] Detection error: {exc}")
            return []

    # ── Scene Description (CLIP/BLIP) ─────────────────────────────────────────

    def describe_scene(self, frame=None) -> str:
        """
        Generate a natural language description of the current scene.

        Requires: pip install transformers pillow torch
        """
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return "No camera feed available."

        # Lazy-load BLIP
        if self._clip is None:
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration
                self._clip = {
                    "processor": BlipProcessor.from_pretrained(
                        "Salesforce/blip-image-captioning-base"
                    ),
                    "model": BlipForConditionalGeneration.from_pretrained(
                        "Salesforce/blip-image-captioning-base"
                    ),
                }
                print("  [VISION] BLIP captioning model loaded.")
            except ImportError:
                return "[Vision module not installed. Run: pip install transformers pillow torch]"
            except Exception as exc:
                return f"[Vision model load failed: {exc}]"

        try:
            from PIL import Image
            import numpy as np

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            inputs = self._clip["processor"](img, return_tensors="pt")
            out = self._clip["model"].generate(**inputs, max_new_tokens=50)
            caption = self._clip["processor"].decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as exc:
            return f"[Caption failed: {exc}]"

    # ── QR Code scanning ──────────────────────────────────────────────────────

    def scan_qr(self, frame=None) -> str | None:
        """
        Scan for QR codes in the current frame.
        Returns decoded data string, or None.

        Requires: pip install pyzbar pillow
        """
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return None

        try:
            from pyzbar import pyzbar
            codes = pyzbar.decode(frame)
            if codes:
                return codes[0].data.decode("utf-8")
        except ImportError:
            print("  [VISION] pyzbar not installed. Run: pip install pyzbar")
        except Exception as exc:
            print(f"  [VISION] QR scan error: {exc}")
        return None

    # ── Screenshot analysis ───────────────────────────────────────────────────

    def capture_screen(self):
        """
        Take a screenshot of the primary display.
        Returns numpy array or None.

        Requires: pip install pillow
        """
        try:
            from PIL import ImageGrab
            import numpy as np
            screenshot = ImageGrab.grab()
            return np.array(screenshot)
        except ImportError:
            print("  [VISION] Pillow not installed. Run: pip install pillow")
            return None
        except Exception as exc:
            print(f"  [VISION] Screenshot failed: {exc}")
            return None
