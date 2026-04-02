
import os
import sys
from PIL import Image
import traceback

# Add app to path
sys.path.append(os.getcwd())

from app.enhancer import get_upscaler, upscale_image

def test_resize():
    log_file = open("verify_resize_result.txt", "w")
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")
        
    log("Testing image resizing...")
    
    # Create a dummy image
    img = Image.new('RGB', (50, 50), color = 'blue')
    
    # Ensure model is checked/loaded
    try:
        get_upscaler()
    except:
        pass # Will be handled in upscale_image or printed

    test_cases = [1, 2, 4]
    
    for scale in test_cases:
        try:
            log(f"--- Testing Scale {scale}x ---")
            enhanced = upscale_image(img, scale_factor=scale)
            
            expected_size = (50 * scale, 50 * scale)
            log(f"Input size: {img.size}")
            log(f"Target scale: {scale}x")
            log(f"Output size: {enhanced.size}")
            
            if enhanced.size == expected_size:
                log(f"SUCCESS: Scale {scale}x produced correct size {enhanced.size}")
            else:
                log(f"FAILED: Scale {scale}x produced {enhanced.size}, expected {expected_size}")
                
        except Exception as e:
            log(f"FAILED: Error during scale {scale}x: {e}")
            traceback.print_exc(file=log_file)
    
    log_file.close()

if __name__ == "__main__":
    test_resize()
