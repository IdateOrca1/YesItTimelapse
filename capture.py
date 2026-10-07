import mss
import pygetwindow as gw

sct = mss.mss()

def get_target_window(app_keyword=""):
    """ค้นหาหน้าต่างโปรแกรมที่ต้องการ ถ้าไม่ระบุจะดึง Active Window"""
    if app_keyword:
        windows = gw.getWindowsWithTitle(app_keyword)
        if windows and not windows[0].isMinimized:
            return windows[0]
    return gw.getActiveWindow()

def capture_window_frame(window):
    """แคปภาพเฉพาะพิกัดของหน้าต่างเป้าหมาย"""
    if not window or window.isMinimized or window.width <= 0 or window.height <= 0:
        return None
        
    bbox = {
        "top": max(0, window.top),
        "left": max(0, window.left),
        "width": window.width,
        "height": window.height
    }
    return sct.grab(bbox)