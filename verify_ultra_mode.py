
import os
import sys
import time
from PIL import Image, ImageChops
import numpy as np

sys.path.append(os.getcwd())
from app.enhancer import get_upscaler
from app.main import enhance_image

def verify_ultra_mode():
    print("Verifying Ultra Quality Mode...")
    
    upscaler = get_upscaler()
    if not upscaler.model_loaded:
        print("Model not loaded!")
        return

    # Create test image
    img = Image.new('RGB', (100, 100), color=(100, 150, 200))
    # Add some noise/detail
    arr = np.array(img)
    noise = np.random.randint(0, 50, arr.shape, dtype='uint8')
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # 1. Run Normal Mode (x2 path likely)
    print("\n--- Normal Mode ---")
    start = time.time()
    out_normal = upscaler.upscale_with_ai(img, scale_factor=2, ultra_mode=False)
    time_normal = time.time() - start
    print(f"Normal Time: {time_normal:.4f}s")
    
    # 2. Run Ultra Mode (Forces x4 + TTA)
    print("\n--- Ultra Mode ---")
    start = time.time()
    out_ultra = upscaler.upscale_with_ai(img, scale_factor=2, ultra_mode=True)
    time_ultra = time.time() - start
    print(f"Ultra Time: {time_ultra:.4f}s")
    
    # Checks
    # Ultra should be significantly slower (x4 model + TTA = ~8x slower than x2)
    if time_ultra > time_normal * 2:
        print("SUCCESS: Ultra mode is taking more time (implies TTA/x4 usage)")
    else:
        print("WARNING: Ultra mode time difference is small")
        
    # Check if outputs are different
    diff = ImageChops.difference(out_normal, out_ultra)
    if diff.getbbox():
        print("SUCCESS: Output images are different (TTA applied)")
    else:
        print("FAILED: Output images are identical")
        
    # Check visual quality (contrast)
    std_normal = np.std(np.array(out_normal))
    std_ultra = np.std(np.array(out_ultra))
    print(f"Normal StdDev: {std_normal:.2f}")
    print(f"Ultra StdDev: {std_ultra:.2f}")
    
    if std_ultra > std_normal:
        print("SUCCESS: Ultra mode has higher local contrast")

if __name__ == "__main__":
    verify_ultra_mode()
