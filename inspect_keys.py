
import torch
import sys
import os

def inspect_model():
    model_path = 'models/RealESRGAN_x2.pth'
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        return

    try:
        checkpoint = torch.load(model_path, map_location='cpu')
        if 'params_ema' in checkpoint:
            print("Found 'params_ema' key. Using it.")
            state_dict = checkpoint['params_ema']
        else:
            state_dict = checkpoint
            
        with open('model_keys_dump.txt', 'w') as f:
            f.write(f"Keys in model: {len(state_dict.keys())}\n")
            keys = list(state_dict.keys())
            
            # Print first few keys
            f.write("First 10 keys:\n")
            for k in keys[:10]:
                f.write(f"{k}\n")
                
            # Check for upsampling keys
            f.write("\nUpsampling keys:\n")
            upsample_keys = [k for k in keys if 'up' in k or 'shuf' in k or 'body' in k]
            for k in upsample_keys:
                 f.write(f"{k}: {state_dict[k].shape}\n")
        print("Done writing to model_keys_dump.txt")
                
    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
    inspect_model()
