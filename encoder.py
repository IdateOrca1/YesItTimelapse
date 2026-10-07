import subprocess
import os

def export_timelapse(output_name="timelapse_output.mp4", fps=60, frame_pattern="temp_frames/frame_%05d.png"):
    """เรียก FFmpeg เพื่อรวมรูปเป็นไฟล์ .mp4 H.264"""
    if not os.path.exists("temp_frames") or not os.listdir("temp_frames"):
        print("[!] No frames to export.")
        return
        
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        output_name
    ]
    
    print("[*] Encoding timelapse...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"[+] Saved timelapse to {output_name}")