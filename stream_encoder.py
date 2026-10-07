import subprocess
import os
import sys

def get_ffmpeg_path():
    """ค้นหา ffmpeg.exe ในทุกโฟลเดอร์ของ PyInstaller และระบบ"""
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(exe_dir, "_internal", "ffmpeg.exe"),
        os.path.join(exe_dir, "ffmpeg.exe"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "ffmpeg.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe"),
        "ffmpeg"
    ]
    
    for p in possible_paths:
        if p and (os.path.exists(p) or p == "ffmpeg"):
            return p
            
    return "ffmpeg"

class MemoryStreamEncoder:
    def __init__(self, output_name="Yes_It_Timelapse.mp4", fps=30):
        self.output_name = output_name
        self.fps = fps
        self.process = None
        self.width = None
        self.height = None

    def start_stream(self, width: int, height: int):
        self.width = width
        self.height = height
        ffmpeg_bin = get_ffmpeg_path()

        cmd = [
            ffmpeg_bin, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-crf", "22",
            self.output_name
        ]

        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW

        # ใช้ DEVNULL แทน PIPE ทั้งหมดเพื่อไม่ให้ Buffer ล้นและค้างที่ wait()
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
        print(f"[*] FFmpeg launched: {ffmpeg_bin} -> {self.output_name}")

    def push_frame(self, raw_rgb_bytes: bytes):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(raw_rgb_bytes)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                print(f"[!] Pipe error: {e}")

    def close(self):
        """ส่ง EOF ไปยัง stdin และรอให้ FFmpeg คืนค่าอย่างรวดเร็ว"""
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.flush()
                    self.process.stdin.close()  # ส่ง EOF จบวิดีโอ
                self.process.communicate(timeout=5)  # ใช้ communicate แทน wait() เพื่อดึง I/O ให้หมด
            except Exception as e:
                print(f"[!] Force closing process: {e}")
                self.process.kill()
            self.process = None
            print(f"[+] Finalized: {self.output_name}")