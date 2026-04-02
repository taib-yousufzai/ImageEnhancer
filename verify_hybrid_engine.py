
import os
import sys
import time
from PIL import Image
import numpy as np

sys.path.append(os.getcwd())
from app.enhancer import get_upscaler, upscale_image

def verify_hybrid_engine():
    log_file = open("verify_hybrid_engine_result.txt", "w")
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")
        
    try:
        log("Verifying Hybrid Engine...")
        
        # 1. Load Models
        start_load = time.time()
        upscaler = get_upscaler()
        load_time = time.time() - start_load
        
        if upscaler.model_x2 is not None and upscaler.model_x4 is not None:
            log(f"SUCCESS: Both models loaded in {load_time:.2f}s")
        else:
            log("FAILED: Models not loaded correctly")
            return

        # Create test image 100x100
        img = Image.new('RGB', (100, 100), color=(100, 150, 200))
        
        # 2. Test x2 Path (Scale = 2)
        log("\n--- Testing x2 Path (Scale=2) ---")
        start_x2 = time.time()
        out_x2 = upscale_image(img, scale_factor=2)
        time_x2 = time.time() - start_x2
        log(f"Time (x2): {time_x2:.4f}s")
        log(f"Output Size: {out_x2.size}")
        if out_x2.size == (200, 200):
             log("SUCCESS: Size correct")
        
        # 3. Test x4 Path (Scale = 4)
        log("\n--- Testing x4 Path (Scale=4) ---")
        start_x4 = time.time()
        out_x4 = upscale_image(img, scale_factor=4)
        time_x4 = time.time() - start_x4
        log(f"Time (x4): {time_x4:.4f}s")
        log(f"Output Size: {out_x4.size}")
        if out_x4.size == (400, 400):
             log("SUCCESS: Size correct")
             
        # Compare speeds
        if time_x2 < time_x4:
            ratio = time_x4 / time_x2
            log(f"\nSUCCESS: x2 path is {ratio:.1f}x faster than x4 path")
        else:
            log("\nWARNING: x2 path was not faster (unexpected)")

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc(file=log_file)
    finally:
        log_file.close()

if __name__ == "__main__":
    verify_hybrid_engine()
