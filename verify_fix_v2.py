
import os
import sys
from PIL import Image
import numpy as np
import traceback

# Add app to path
sys.path.append(os.getcwd())

from app.enhancer import get_upscaler, upscale_image

def test_enhancement():
    log_file = open("verify_result_v2.txt", "w")
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")
        
    log("Testing image enhancement...")
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    
    # Test upscaler loading
    try:
        upscaler = get_upscaler()
        if not upscaler.model_loaded:
            log("FAILED: Model not loaded")
            # Try to force load to capture print output (but prints go to stdout)
            # We can't easily capture prints from modules without redirecting stdout
            # But let's check validation logic
            pass
        else:
             log("SUCCESS: Model loaded")
    except Exception as e:
        log(f"FAILED: Error loading upscaler: {e}")
        traceback.print_exc(file=log_file)
        return

    # Test enhancement
    try:
        enhanced = upscale_image(img)
        log(f"Original size: {img.size}")
        log(f"Enhanced size: {enhanced.size}")
        
        # Check color
        enhanced_np = np.array(enhanced)
        mean_color = np.mean(enhanced_np, axis=(0, 1))
        log(f"Original Color: (255, 0, 0)")
        log(f"Enhanced Mean Color: {mean_color}")
        
        if mean_color[0] > mean_color[1] and mean_color[0] > mean_color[2]:
            log("SUCCESS: Output is Red-ish")
        else:
            log("FAILED: Output color is wrong (Blue/Green dominant?)")
            
        if enhanced.size == (200, 200):
            log("SUCCESS: Image enhanced to 2x size")
        else:
            log(f"FAILED: Incorrect output size {enhanced.size}")
            
    except Exception as e:
        log(f"FAILED: Error during enhancement: {e}")
        traceback.print_exc(file=log_file)
    
    log_file.close()

if __name__ == "__main__":
    test_enhancement()
