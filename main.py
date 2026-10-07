import time
import os
import shutil
from pynput import mouse, keyboard
from capture import get_target_window, capture_window_frame
from encoder import export_timelapse
import mss.tools

# Config
TARGET_KEYWORD = ""     # เว้นว่างไว้เพื่อจับทุกหน้าต่างที่ Active หรือใส่ชื่อ เช่น "Photoshop", "Paint"
MIN_INTERVAL = 0.8      # หน่วงเวลาขั้นต่ำ (วินาที) กันการคลิกรัว
frame_idx = 0
last_time = 0
is_recording = True

# สร้างโฟลเดอร์ชั่วคราว
if os.path.exists("temp_frames"):
    shutil.rmtree("temp_frames")
os.makedirs("temp_frames", exist_ok=True)

def on_click(x, y, button, pressed):
    global last_time, frame_idx, is_recording
    if not is_recording:
        return
        
    # ดักจังหวะปล่อยปากกา/เมาส์ (Button Up)
    if not pressed and button == mouse.Button.left:
        now = time.time()
        if now - last_time >= MIN_INTERVAL:
            win = get_target_window(TARGET_KEYWORD)
            if win:
                img = capture_window_frame(win)
                if img:
                    filepath = f"temp_frames/frame_{frame_idx:05d}.png"
                    mss.tools.to_png(img.rgb, img.size, output=filepath)
                    frame_idx += 1
                    last_time = now
                    print(f"[*] Captured frame #{frame_idx} ({win.title[:25]}...)")

def on_press_key(key):
    global is_recording
    # กดปุ่ม F9 เพื่อหยุดบันทึกและ Render วิดีโอ
    if key == keyboard.Key.f9:
        print("\n[!] Stopping recording and rendering...")
        is_recording = False
        export_timelapse("Yes_It_Timelapse.mp4", fps=30)
        return False  # หยุด Keyboard Listener

print("=== Yes! It Timelapse Started ===")
print("[*] Draw normally. Press [F9] to Finish & Render Video.\n")

mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

with keyboard.Listener(on_press=on_press_key) as key_listener:
    key_listener.join()

mouse_listener.stop()
print("=== Done! ===")