# 🎬 Yes! It Timelapse

A lightweight, zero-disk-lag desktop timelapse recorder tailored for digital artists. Automatically captures strokes on pen/mouse release and streams frames directly to FFmpeg without creating temporary image files.

---

## ✨ Key Features

- **Smart Pen-Lift Capture:** Records frames only when you lift the pen/mouse button (`ButtonRelease`), avoiding redundant static frames.
- **In-Memory Pipe Encoding:** Streams raw pixel buffers directly into FFmpeg `stdin`—no temp PNG files and instant video exports.
- **Window Target Filtering:** Captures only the selected application window (e.g., Clip Studio Paint, Photoshop, Paint) and auto-pauses when switching apps.
- **Adaptive Frame Resizing:** Auto-adjusts frame dimensions on the fly to prevent encoding errors if the target window is resized.
- **Modern GUI:** Built with CustomTkinter for a sleek dark-mode control interface.

---

## 🛠️ Requirements

- **OS:** Windows 10 / 11
- **Python:** 3.10+
- **FFmpeg:** Installed and added to system `PATH`

---
