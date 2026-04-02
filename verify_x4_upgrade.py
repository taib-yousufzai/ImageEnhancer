
import os
import sys
from PIL import Image
import numpy as np
import traceback

sys.path.append(os.getcwd())
from app.enhancer import get_upscaler, upscale_image

def verify_x4_upgrade():
    log_file = open("verify_x4_upgrade_result.txt", "w")
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")
        
    try:
        log("Verifying Real-ESRGAN x4plus upgrade...")
        
        # 1. Check Model File
        model_path = "models/RealESRGAN_x4plus.pth"
        if os.path.exists(model_path):
            log(f"SUCCESS: Model file found at {model_path} ({os.path.getsize(model_path)/1024/1024:.2f} MB)")
        else:
            log(f"FAILED: Model file not found at {model_path}")
            return

        # 2. Check Model Loading
        log("Loading model...")
        upscaler = get_upscaler()
        if upscaler.model_loaded:
            log("SUCCESS: Model loaded into memory")
        else:
            log("FAILED: Model failed to load")
            return

        # 3. Test Enhancement (Color & Size)
        # Create small red image 50x50
        img = Image.new('RGB', (50, 50), color=(255, 0, 0))
        
        # Test 4x (Native)
        log("Testing 4x upscale (Native)...")
        enhanced_4x = upscale_image(img, scale_factor=4)
        if enhanced_4x.size == (200, 200):
            log("SUCCESS: 4x output size is correct (200, 200)")
        else:
            log(f"FAILED: 4x output size is {enhanced_4x.size}, expected (200, 200)")
            
        # Test 2x (Downscaled)
        log("Testing 2x upscale (Downscaled from 4x)...")
        enhanced_2x = upscale_image(img, scale_factor=2)
        if enhanced_2x.size == (100, 100):
             log("SUCCESS: 2x output size is correct (100, 100)")
        else:
             log(f"FAILED: 2x output size is {enhanced_2x.size}, expected (100, 100)")

        # Test Color Accuracy on 4x
        arr = np.array(enhanced_4x)
        mean_color = np.mean(arr, axis=(0, 1))
        log(f"Mean Color: {mean_color}")
        if mean_color[0] > 200 and mean_color[1] < 30 and mean_color[2] < 30:
            log("SUCCESS: Color preserved (Red)")
        else:
            log("FAILED: Color distortion detected")

    except Exception as e:
        log(f"ERROR: {e}")
        traceback.print_exc(file=log_file)
    finally:
        log_file.close()

if __name__ == "__main__":
    verify_x4_upgrade()
