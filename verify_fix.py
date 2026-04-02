
import os
import sys
from PIL import Image
import numpy as np

# Add app to path
sys.path.append(os.getcwd())

from app.enhancer import get_upscaler, upscale_image

def test_enhancement():
    print("Testing image enhancement...")
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    
    # Test upscaler loading
    try:
        upscaler = get_upscaler()
        if not upscaler.model_loaded:
            print("FAILED: Model not loaded")
            return
        print("SUCCESS: Model loaded")
    except Exception as e:
        print(f"FAILED: Error loading upscaler: {e}")
        return


    # Test enhancement
    try:
        enhanced = upscale_image(img)
        print(f"Original size: {img.size}")
        print(f"Enhanced size: {enhanced.size}")
        
        # Check color
        # Original is Red (255, 0, 0)
        # enhanced should be Red
        enhanced_np = np.array(enhanced)
        mean_color = np.mean(enhanced_np, axis=(0, 1))
        print(f"Original Color: (255, 0, 0)")
        print(f"Enhanced Mean Color: {mean_color}")
        
        # Check if R is dominant
        if mean_color[0] > mean_color[1] and mean_color[0] > mean_color[2]:
            print("SUCCESS: Output is Red-ish")
        else:
            print("FAILED: Output color is wrong (Blue/Green dominant?)")
            
        if enhanced.size == (200, 200):
            print("SUCCESS: Image enhanced to 2x size")
        else:
            print(f"FAILED: Incorrect output size {enhanced.size}")
            
    except Exception as e:
        print(f"FAILED: Error during enhancement: {e}")

if __name__ == "__main__":
    test_enhancement()
