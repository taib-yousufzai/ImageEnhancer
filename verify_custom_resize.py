
import os
import sys
from PIL import Image
import traceback

# Add app to path
sys.path.append(os.getcwd())

from app.enhancer import get_upscaler, upscale_image

def test_custom_resize():
    log_file = open("verify_custom_resize_result.txt", "w")
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")
        
    log("Testing custom image resizing...")
    
    # Create a dummy image 100x50 (2:1 aspect ratio)
    img = Image.new('RGB', (100, 50), color = 'blue')
    
    # Ensure model is checked/loaded
    try:
        get_upscaler()
    except:
        pass 

    test_cases = [
        {"name": "Scale 2x", "args": {"scale_factor": 2}, "expected": (200, 100)},
        {"name": "Custom W=300", "args": {"target_width": 300}, "expected": (300, 150)}, # AR maintained
        {"name": "Custom H=200", "args": {"target_height": 200}, "expected": (400, 200)}, # AR maintained
        {"name": "Custom 150x150", "args": {"target_width": 150, "target_height": 150}, "expected": (150, 150)}, # Exact
    ]
    
    for case in test_cases:
        try:
            log(f"--- Testing {case['name']} ---")
            enhanced = upscale_image(img, **case['args'])
            
            log(f"Input size: {img.size}")
            log(f"Args: {case['args']}")
            log(f"Output size: {enhanced.size}")
            
            if enhanced.size == case['expected']:
                log(f"SUCCESS: {case['name']} produced correct size {enhanced.size}")
            else:
                log(f"FAILED: {case['name']} produced {enhanced.size}, expected {case['expected']}")
                
        except Exception as e:
            log(f"FAILED: Error during {case['name']}: {e}")
            traceback.print_exc(file=log_file)
    
    log_file.close()

if __name__ == "__main__":
    test_custom_resize()
