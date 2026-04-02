
import os
import requests
from pathlib import Path

def download_x2_model():
    # URL for Real-ESRGAN x2plus model
    url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    file_path = models_dir / "RealESRGAN_x2plus.pth"
    
    if file_path.exists():
        print(f"Model already exists at {file_path}")
        return

    print(f"Downloading {url} to {file_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete!")
    except Exception as e:
        print(f"Failed to download model: {e}")
        if file_path.exists():
            file_path.unlink()

if __name__ == "__main__":
    download_x2_model()
