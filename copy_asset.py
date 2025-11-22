import shutil
import os

src = r"C:\Users\acer\.gemini\antigravity\brain\c14350fd-3fc1-422e-8ea6-196e0fc3dbeb\splash_background_1763813086169.png"
dst = r"c:\Users\acer\Documents\Gravity\assets\splash_background.png"

try:
    shutil.copy(src, dst)
    print("Copy success")
except Exception as e:
    print(f"Copy failed: {e}")
