"""
Image upscaling module for AI Image Enhancer API.

This module provides AI-powered image upscaling using Real-ESRGAN architecture
with high-quality neural network-based enhancement.
"""

import torch
import torch.nn as nn
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import os
import urllib.request
from pathlib import Path
import threading
import gc


class RRDBNet(nn.Module):
    """
    Real-ESRGAN network architecture (simplified version).
    Residual in Residual Dense Block Network for image super-resolution.
    """
    
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, scale=2):
        super(RRDBNet, self).__init__()
        self.scale = scale
        
        # First convolution
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        
        # Body: RRDB blocks
        self.body = nn.Sequential(*[RRDBBlock(num_feat) for _ in range(num_block)])
        
        # Body convolution (was missing)
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Upsampling layers
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        if scale == 4:
            self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Final convolution
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        
        # Activation
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
    
    def forward(self, x):
        feat = self.conv_first(x)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        
        # Upsample
        feat = self.lrelu(self.conv_up1(nn.functional.interpolate(feat, scale_factor=2, mode='nearest')))
        if self.scale == 4:
            feat = self.lrelu(self.conv_up2(nn.functional.interpolate(feat, scale_factor=2, mode='nearest')))
        
        out = self.conv_last(self.lrelu(self.conv_hr(feat)))
        return out


class RRDBBlock(nn.Module):
    """Residual in Residual Dense Block"""
    
    def __init__(self, num_feat=64, num_grow_ch=32):
        super(RRDBBlock, self).__init__()
        self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)
    
    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class ResidualDenseBlock(nn.Module):
    """Residual Dense Block"""
    
    def __init__(self, num_feat=64, num_grow_ch=32):
        super(ResidualDenseBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
    
    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RealESRGANUpscaler:
    """
    Real-ESRGAN based AI upscaler for high-quality image enhancement.
    Uses a pre-trained model for 2x upscaling with superior quality.
    """
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_x2 = None
        self.model_x4 = None
        self.model_loaded = False
        self.path_x2 = Path('models/RealESRGAN_x2plus.pth')
        self.path_x4 = Path('models/RealESRGAN_x4plus.pth')
        self._lock = threading.Lock()
        
    def _load_single_model(self, path, scale_arch, in_channels=3):
        """Helper to load a single model."""
        try:
            model = RRDBNet(num_in_ch=in_channels, num_out_ch=3, num_feat=64, num_block=23, scale=4)
            
            if path.exists():
                print(f"Loading model from {path}")
                checkpoint = torch.load(path, map_location=self.device)
                state_dict = checkpoint['params_ema'] if 'params_ema' in checkpoint else checkpoint
                model.load_state_dict(state_dict, strict=True)
            else:
                print(f"Weights not found at {path}. Using random init.")
            
            model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"Failed to load model from {path}: {e}")
            return None

    def load_model(self):
        """Load both Real-ESRGAN models with thread safety."""
        with self._lock:
            if self.model_loaded:
                return
            
            try:
                self.path_x2.parent.mkdir(parents=True, exist_ok=True)
                
                # Load x2 model (Requires pixel unshuffle -> 12 channels)
                self.model_x2 = self._load_single_model(self.path_x2, scale_arch=4, in_channels=12)
                
                # Load x4 model (Standard -> 3 channels)
                self.model_x4 = self._load_single_model(self.path_x4, scale_arch=4, in_channels=3)
                
                if self.model_x2 is not None and self.model_x4 is not None:
                    self.model_loaded = True
                    print(f"Hybrid Real-ESRGAN Engine loaded successfully on {self.device}")
                else:
                    self.model_loaded = False
                    print("Failed to load one or both models.")
                
            except Exception as e:
                print(f"Error loading Real-ESRGAN models: {e}")
                self.model_loaded = False
                raise
    
    def upscale_with_ai(self, image: Image.Image, scale_factor: int = 2, target_width: int = None, target_height: int = None, ultra_mode: bool = False, progress_callback=None) -> Image.Image:
        """
        Upscale image using Real-ESRGAN AI enhancement with natural post-processing.
        
        Args:
            image: PIL Image object
            scale_factor: Upscaling factor (default: 2)
            target_width: Custom target width (overrides scale)
            target_height: Custom target height
            ultra_mode: Enable Test-Time Augmentation and maximum quality
            progress_callback: Optional function(progress_percent, message)
            
        Returns:
            Upscaled and naturally enhanced PIL Image
        """
        if progress_callback:
            progress_callback(0, "Initializing AI Engine...")
            
        if not self.model_loaded:
            if progress_callback: progress_callback(5, "Loading Models (This might take a moment)...")
            self.load_model() # Ensure loaded
            if not self.model_loaded:
                 raise RuntimeError("Real-ESRGAN models not loaded")
        
        if progress_callback:
            progress_callback(10, "Analyzing Image & Calculating Dimensions...")
        
        # Determine valid target dimensions to choose model
        target_w, target_h = None, None
        orig_w, orig_h = image.size
        
        # Logic to calculate target dimensions first (needed for model selection)
        if target_width or target_height:
             if target_width and target_height:
                 target_w, target_h = target_width, target_height
             elif target_width:
                 ratio = orig_h / orig_w
                 target_w = target_width
                 target_h = int(target_width * ratio)
             else:
                 ratio = orig_w / orig_h
                 target_h = target_height
                 target_w = int(target_height * ratio)
        else:
            target_w = orig_w * scale_factor
            target_h = orig_h * scale_factor
            
        # Select Model
        # In Ultra Mode, ALWAYS use x4 model for best quality
        if ultra_mode:
            model_to_use = self.model_x4
            use_x2 = False
        else:
            effective_scale = target_w / orig_w
            use_x2 = effective_scale <= 2.1
            model_to_use = self.model_x2 if use_x2 else self.model_x4
        
        # Helper for inference (now with strict resource management)
        def _run_inference(img_pil):
             img_array = np.array(img_pil).astype(np.float32) / 255.0
             if len(img_array.shape) == 2:
                 img_array = np.stack([img_array] * 3, axis=2)
             
             img_tensor = torch.from_numpy(np.transpose(img_array, (2, 0, 1))).float()
             img_tensor = img_tensor.unsqueeze(0).to(self.device)
             
             if use_x2:
                 img_tensor = nn.functional.pixel_unshuffle(img_tensor, 2)
                 
             with torch.no_grad():
                 with self._lock: # Ensure only one inference task runs at a time
                    output = model_to_use(img_tensor)
                  
             output_array = output.squeeze(0).cpu().numpy()
             output_array = np.transpose(output_array, (1, 2, 0))
             output_array = np.clip(output_array * 255.0, 0, 255).astype(np.uint8)
             
             # Clean up GPU memory immediately
             del img_tensor
             if self.device.type == 'cuda':
                 torch.cuda.empty_cache()
             gc.collect()
             
             return output_array

        # Run Inference (with TTA if Ultra Mode)
        if ultra_mode:
            if progress_callback: progress_callback(30, "Running AI Inference (Pass 1/2)...")
            # 1. Normal
            out_1 = _run_inference(image)
            
            if progress_callback: progress_callback(60, "Running AI Inference (Pass 2/2 - TTA)...")
            # 2. Horizontal Flip
            img_flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
            out_2_flipped = _run_inference(img_flipped)
            out_2 = np.fliplr(out_2_flipped) # Flip back
            
            if progress_callback: progress_callback(80, "Merging & Refining Details...")
            # Average
            final_output_array = (out_1.astype(np.float32) + out_2.astype(np.float32)) / 2.0
            final_output_array = np.clip(final_output_array, 0, 255).astype(np.uint8)
            enhanced_image = Image.fromarray(final_output_array)
            # Free memory
            del out_1, out_2, final_output_array
        else:
            if progress_callback: progress_callback(40, "Running AI Inference...")
            out = _run_inference(image)
            enhanced_image = Image.fromarray(out)
            del out
        
        if progress_callback: progress_callback(90, "Applying Final Polish...")
        # Final Resize to exact target
        if enhanced_image.size != (target_w, target_h):
             enhanced_image = enhanced_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
        # Apply mild post-processing
        # Use slightly stronger parameters for Ultra Mode
        enhanced_image = self.apply_post_processing(enhanced_image, ultra=ultra_mode)
        
        if progress_callback: progress_callback(100, "Done!")
            
        return enhanced_image
    
    def apply_post_processing(self, image: Image.Image, ultra: bool = False) -> Image.Image:
        """
        Apply mild post-processing to make the image pop.
        - Unsharp Mask for crisp edges
        - Slight Contrast boost
        """
        # 1. Unsharp Mask
        # Ultra: Radius=1.5, Percent=80% (Stronger)
        # Normal: Radius=1.0, Percent=50%
        radius = 1.5 if ultra else 1.0
        percent = 80 if ultra else 50
        
        image = image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=3))
        
        # 2. Slight Contrast Boost
        # Ultra: +10%
        # Normal: +5%
        factor = 1.10 if ultra else 1.05
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(factor)
        
        return image


# Global upscaler instance
_upscaler = None


def get_upscaler():
    """Get or create the global upscaler instance."""
    global _upscaler
    if _upscaler is None:
        _upscaler = RealESRGANUpscaler()
        _upscaler.load_model()
    return _upscaler


def upscale_image(image: Image.Image, scale_factor: int = 2, target_width: int = None, target_height: int = None, ultra_mode: bool = False, progress_callback=None) -> Image.Image:
    """
    Upscales image by the specified factor using high-quality AI-enhanced upscaling.
    Converts to RGB if necessary.
    
    Args:
        image: PIL Image object to upscale
        scale_factor: Multiplier for dimensions (default: 2)
        ultra_mode: Enable Test-Time Augmentation
        progress_callback: Optional progress callback
    
    Returns:
        Upscaled Image object in RGB mode
    
    Requirements:
        - 2.1: Upscale to exactly 4x original dimensions
        - 2.3: Convert to RGB mode before upscaling
    """
    # Use the AI upscaler
    upscaler = get_upscaler()
    try:
        return upscaler.upscale_with_ai(image, scale_factor, target_width, target_height, ultra_mode, progress_callback)
    except Exception as e:
        print(f"Error using AI upscaler: {e}. Falling back to standard resize.")
        
        # Fallback to standard resize if AI fails
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL to numpy for OpenCV processing
        img_array = np.array(image)
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Calculate new dimensions
        height, width = img_array.shape[:2]
        
        if target_width or target_height:
             if target_width and target_height:
                 new_width, new_height = target_width, target_height
             elif target_width:
                 ratio = height / width
                 new_width = target_width
                 new_height = int(target_width * ratio)
             else:
                 ratio = width / height
                 new_height = target_height
                 new_width = int(target_height * ratio)
        else:
            new_width = width * scale_factor
            new_height = height * scale_factor
        
        # Use high-quality bicubic interpolation for upscaling
        upscaled = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Convert back to RGB and PIL Image
        enhanced = cv2.cvtColor(upscaled, cv2.COLOR_BGR2RGB)
        return Image.fromarray(enhanced)
