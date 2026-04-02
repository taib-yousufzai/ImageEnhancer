
import os
import sys
from PIL import Image, ImageChops
import numpy as np

sys.path.append(os.getcwd())
from app.enhancer import get_upscaler
from PIL import ImageEnhance, ImageFilter # Import these for manual simulation if needed

def verify_post_processing():
    print("Verifying Post-Processing...")
    
    upscaler = get_upscaler()
    
    # Create a test image with some details (noise) to sharpen
    img = Image.new('RGB', (100, 100), color=(128, 128, 128))
    # Add some noise
    arr = np.array(img)
    noise = np.random.randint(0, 20, arr.shape, dtype='uint8')
    arr = arr + noise
    img = Image.fromarray(np.clip(arr, 0, 255).astype('uint8'))
    
    print("Original stats:", np.mean(np.array(img)), np.std(np.array(img)))
    
    # Apply post-processing
    processed = upscaler.apply_post_processing(img)
    
    print("Processed stats:", np.mean(np.array(processed)), np.std(np.array(processed)))
    
    # Check if contrast increased (std dev should increase)
    orig_std = np.std(np.array(img))
    proc_std = np.std(np.array(processed))
    
    if proc_std > orig_std:
        print(f"SUCCESS: Contrast/Detail increased (StdDev: {orig_std:.2f} -> {proc_std:.2f})")
    else:
        print(f"FAILED: Contrast did not increase (StdDev: {orig_std:.2f} -> {proc_std:.2f})")
        
    # Check if image is not drastically changed (it should be subtle)
    diff = ImageChops.difference(img, processed)
    mean_diff = np.mean(np.array(diff))
    print(f"Mean Difference: {mean_diff:.2f}")
    
    if mean_diff < 10:
        print("SUCCESS: Change is subtle (Mean Difference < 10)")
    else:
        print("WARNING: Change might be too aggressive")

if __name__ == "__main__":
    verify_post_processing()
