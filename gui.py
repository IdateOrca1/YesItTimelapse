import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import os
from datetime import datetime
import mss
from PIL import Image
import win32gui
import win32api
from stream_encoder import MemoryStreamEncoder

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class YesItTimelapseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Yes! It Timelapse")
        self.geometry("400x520")
        self.resizable(False, False)
        self.attributes("-topmost", False)

        # State Variables
        self.is_recording = False
        self.is_paused = False
        self.frame_idx = 0
        self.last_capture_time = 0
        self.min_interval = 0.3
        self.selected_fps = 2  # ค่าเริ่มต้น: Frame-by-frame (2 FPS)
        
        self.window_dict = {} 
        self.target_hwnd = None
        self.worker_thread = None

        self.sct = mss.mss()
        self.encoder = None

        self.save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(self.save_dir):
            self.save_dir = os.getcwd()

        self.target_width = None
        self.target_height = None

        self._build_ui()
        self.refresh_window_list()

    def _build_ui(self):
        # Header
        self.label_title = ctk.CTkLabel(self, text="🎬 Yes! It Timelapse", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=(12, 2))

        # Target Window
        self.label_select = ctk.CTkLabel(self, text="Target Drawing Window:", font=ctk.CTkFont(size=12))
        self.label_select.pack(pady=(4, 0))

        self.window_dropdown = ctk.CTkOptionMenu(self, values=["Refreshing..."], width=320, command=self.on_select_window)
        self.window_dropdown.pack(pady=4)

        self.btn_refresh = ctk.CTkButton(self, text="🔄 Refresh Windows", width=120, height=22, command=self.refresh_window_list, fg_color="gray30")
        self.btn_refresh.pack(pady=(0, 6))

        # Save Location
        self.label_dir = ctk.CTkLabel(self, text="Save Location:", font=ctk.CTkFont(size=12))
        self.label_dir.pack(pady=(0, 2))

        self.frame_dir = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dir.pack(pady=(0, 6))

        self.entry_dir = ctk.CTkEntry(self.frame_dir, width=235, height=28)
        self.entry_dir.insert(0, self.save_dir)
        self.entry_dir.pack(side="left", padx=(0, 5))

        self.btn_browse = ctk.CTkButton(self.frame_dir, text="📁 Browse", width=75, height=28, command=self.browse_output_dir)
        self.btn_browse.pack(side="left")

        # Frame Rate (FPS) Dropdown
        self.label_fps = ctk.CTkLabel(self, text="Timelapse Frame Rate (FPS):", font=ctk.CTkFont(size=12))
        self.label_fps.pack(pady=(0, 2))

        fps_options = [
            "1 FPS (Slow / Step-by-Step)",
            "2 FPS (Detailed Preview)",
            "5 FPS (Stop Motion)",
            "10 FPS (Classic Timelapse)",
            "15 FPS (Smooth Slow)",
            "20 FPS (Medium Pace)",
            "25 FPS (PAL Standard)",
            "30 FPS (Standard Video)",
            "60 FPS (Ultra Smooth)"
        ]
        self.fps_dropdown = ctk.CTkOptionMenu(
            self,
            values=fps_options,
            command=self.on_fps_change,
            width=320
        )
        self.fps_dropdown.set("2 FPS (Detailed Preview)")
        self.fps_dropdown.pack(pady=(0, 10))

        # Status & Stats
        self.label_status = ctk.CTkLabel(self, text="Status: Ready", text_color="gray70", font=ctk.CTkFont(size=13))
        self.label_status.pack(pady=2)

        self.label_frames = ctk.CTkLabel(self, text="Frames Captured: 0", font=ctk.CTkFont(size=13, weight="bold"))
        self.label_frames.pack(pady=(0, 10))

        # Action Buttons
        self.btn_toggle_rec = ctk.CTkButton(self, text="▶ Start Recording", width=320, height=38, fg_color="#2EA043", hover_color="#238636", command=self.toggle_recording)
        self.btn_toggle_rec.pack(pady=4)

        self.btn_pause = ctk.CTkButton(self, text="⏸ Pause", width=320, height=30, state="disabled", fg_color="gray40", command=self.toggle_pause)
        self.btn_pause.pack(pady=4)

    def on_fps_change(self, value):
        # ดึงเฉพาะตัวเลขด้านหน้า เช่น '15 FPS (...)' -> 15
        self.selected_fps = int(value.split(" FPS")[0])

    def browse_output_dir(self):
        chosen_dir = filedialog.askdirectory(initialdir=self.save_dir, title="Select Output Folder")
        if chosen_dir:
            self.save_dir = os.path.normpath(chosen_dir)
            self.entry_dir.delete(0, "end")
            self.entry_dir.insert(0, self.save_dir)

    def refresh_window_list(self):
        self.window_dict.clear()
        
        def enum_windows_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if title and w > 150 and h > 150:
                    if title not in ["Yes! It Timelapse", "Settings", "Program Manager"]:
                        display_name = f"{title[:45]}..." if len(title) > 45 else title
                        self.window_dict[display_name] = hwnd
            return True

        win32gui.EnumWindows(enum_windows_callback, None)
        
        options = list(self.window_dict.keys())
        if options:
            self.window_dropdown.configure(values=options)
            self.window_dropdown.set(options[0])
            self.target_hwnd = self.window_dict[options[0]]
        else:
            self.window_dropdown.configure(values=["No Active Windows"])
            self.target_hwnd = None

    def on_select_window(self, choice):
        self.target_hwnd = self.window_dict.get(choice)

    def toggle_recording(self):
        if not self.is_recording:
            if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
                self.label_status.configure(text="⚠️ Please select a window", text_color="#FF7B72")
                return

            custom_path = self.entry_dir.get().strip()
            if os.path.isdir(custom_path):
                self.save_dir = custom_path
            else:
                self.label_status.configure(text="⚠️ Invalid directory path", text_color="#FF7B72")
                return

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = os.path.join(self.save_dir, f"Timelapse_{timestamp_str}.mp4")

            self.is_recording = True
            self.is_paused = False
            self.frame_idx = 0
            self.last_capture_time = 0
            self.target_width = None
            self.target_height = None
            self.current_output_file = output_filepath
            
            self.encoder = MemoryStreamEncoder(output_name=output_filepath, fps=self.selected_fps)

            # Lock UI
            self.btn_toggle_rec.configure(text="⏹ Stop & Save", fg_color="#DA3633", hover_color="#B62324")
            self.btn_pause.configure(state="normal", text="⏸ Pause", fg_color="gray30")
            self.window_dropdown.configure(state="disabled")
            self.btn_refresh.configure(state="disabled")
            self.btn_browse.configure(state="disabled")
            self.entry_dir.configure(state="disabled")
            self.fps_dropdown.configure(state="disabled")
            self.label_status.configure(text=f"🔴 Recording ({self.selected_fps} FPS)...", text_color="#7EE787")
            self.label_frames.configure(text="Frames Captured: 0")

            self.worker_thread = threading.Thread(target=self._mouse_poll_loop, daemon=True)
            self.worker_thread.start()
        else:
            self.is_recording = False
            self.label_status.configure(text="⏳ Finalizing Video...", text_color="#E3B341")
            self.btn_toggle_rec.configure(state="disabled")
            self.btn_pause.configure(state="disabled")

            threading.Thread(target=self._finalize_stream, daemon=True).start()

    def toggle_pause(self):
        if not self.is_recording:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="▶ Resume", fg_color="#1F6FEB")
            self.label_status.configure(text="⏸ Paused", text_color="#E3B341")
        else:
            self.btn_pause.configure(text="⏸ Pause", fg_color="gray30")
            self.label_status.configure(text=f"🔴 Recording ({self.selected_fps} FPS)...", text_color="#7EE787")

    def _is_target_active(self):
        """ตรวจสอบว่าผู้ใช้กำลังใช้งานหน้าต่างเป้าหมายอยู่จริงหรือไม่"""
        if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
            return False

        # ถ้าหน้าต่างถูก Minimize (พับจอ) -> ไม่นับ
        if win32gui.IsIconic(self.target_hwnd):
            return False

        # เช็กหน้าต่างที่กำลัง Active อยู่ข้างหน้าสุด
        active_hwnd = win32gui.GetForegroundWindow()
        if not active_hwnd:
            return False

        # หาหน้าต่างระดับ Root (รองรับ Child Dialog / Sub-canvas ของ Photoshop/Paint)
        root_active = win32gui.GetAncestor(active_hwnd, 2)  # 2 = GA_ROOT
        root_target = win32gui.GetAncestor(self.target_hwnd, 2)

        return (active_hwnd == self.target_hwnd or 
                root_active == self.target_hwnd or 
                root_active == root_target)

    def _mouse_poll_loop(self):
        was_down = False
        VK_LBUTTON = 0x01

        while self.is_recording:
            if self.is_paused:
                time.sleep(0.05)
                continue

            is_down = bool(win32api.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

            # จังหวะปล่อยปุ่มเมาส์ / ยกปากกา
            if was_down and not is_down:
                now = time.time()
                # ต้องเว้นระยะ min_interval และต้องอยู่บนหน้าต่างวาดรูปเท่านั้น
                if (now - self.last_capture_time >= self.min_interval) and self._is_target_active():
                    self._capture_frame()
                    self.last_capture_time = now

            was_down = is_down
            time.sleep(0.015)

    def _capture_frame(self):
        if not self._is_target_active():
            return

        try:
            rect = win32gui.GetWindowRect(self.target_hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                return

            bbox = {
                "top": max(0, top),
                "left": max(0, left),
                "width": width,
                "height": height
            }

            sct_img = self.sct.grab(bbox)
            pil_img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            img_w, img_h = pil_img.size
            if img_w % 2 != 0: img_w -= 1
            if img_h % 2 != 0: img_h -= 1

            if self.target_width is None:
                self.target_width = img_w
                self.target_height = img_h
                self.encoder.start_stream(self.target_width, self.target_height)

            if pil_img.size != (self.target_width, self.target_height):
                pil_img = pil_img.resize((self.target_width, self.target_height))

            self.encoder.push_frame(pil_img.tobytes())
            self.frame_idx += 1
            
            self.after(0, lambda: self.label_frames.configure(text=f"Frames Captured: {self.frame_idx}"))
        except Exception as e:
            print(f"[!] Capture error: {e}")

    def _finalize_stream(self):
        if self.encoder:
            self.encoder.close()
            self.encoder = None

        filename_only = os.path.basename(self.current_output_file)
        
        def reset_ui():
            self.label_status.configure(text=f"✅ Saved: {filename_only}", text_color="#7EE787")
            self.btn_toggle_rec.configure(state="normal", text="▶ Start Recording", fg_color="#2EA043", hover_color="#238636")
            self.window_dropdown.configure(state="normal")
            self.btn_refresh.configure(state="normal")
            self.btn_browse.configure(state="normal")
            self.entry_dir.configure(state="normal")
            self.fps_dropdown.configure(state="normal")

        self.after(0, reset_ui)

if __name__ == "__main__":
    app = YesItTimelapseApp()
    app.mainloop()