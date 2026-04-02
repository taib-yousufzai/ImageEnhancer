"""
Image compression module for converting and optimizing images to various formats.
"""

from io import BytesIO
from PIL import Image


def compress_to_webp(image: Image.Image, max_size_mb: float = 1.0, hd_quality: bool = False) -> bytes:
    """
    Compresses image to WEBP format with size constraint.
    
    Iteratively reduces quality from 95 to 10 by steps of 5 until the output
    size is at or below max_size_mb. If the size cannot be reduced below the
    limit even at quality 10, returns the best effort compression.
    
    Args:
        image: PIL Image object to compress
        max_size_mb: Maximum output size in megabytes (default: 1.0)
        hd_quality: If True, prioritizes quality over size (starts at 95, stops at 85)
    
    Returns:
        Compressed image as bytes in WEBP format
    
    Requirements: 3.1, 3.4
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    
    if hd_quality:
        # HD mode: Start at 95, only reduce to 85 minimum for high quality
        quality = 95
        min_quality = 85
    else:
        # Standard mode: More aggressive compression
        quality = 95
        min_quality = 10
    
    while quality >= min_quality:
        buffer = BytesIO()
        image.save(buffer, format='WEBP', quality=quality)
        size = buffer.tell()
        
        if size <= max_size_bytes:
            return buffer.getvalue()
        
        quality -= 5
    
    # If still too large at minimum quality, return best effort
    return buffer.getvalue()


def compress_to_jpeg(image: Image.Image, max_size_mb: float = 1.0, hd_quality: bool = False) -> bytes:
    """
    Compresses image to JPEG format with size constraint.
    
    Args:
        image: PIL Image object to compress
        max_size_mb: Maximum output size in megabytes (default: 1.0)
        hd_quality: If True, prioritizes quality over size (starts at 95, stops at 85)
    
    Returns:
        Compressed image as bytes in JPEG format
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    
    if hd_quality:
        # HD mode: Start at 95, only reduce to 85 minimum for high quality
        quality = 95
        min_quality = 85
    else:
        # Standard mode: More aggressive compression
        quality = 95
        min_quality = 10
    
    while quality >= min_quality:
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        size = buffer.tell()
        
        if size <= max_size_bytes:
            return buffer.getvalue()
        
        quality -= 5
    
    return buffer.getvalue()


def compress_to_png(image: Image.Image, max_size_mb: float = 10.0, hd_quality: bool = False) -> bytes:
    """
    Compresses image to PNG format with size constraint.
    
    Args:
        image: PIL Image object to compress
        max_size_mb: Maximum output size in megabytes (default: 10.0 for PNG)
        hd_quality: If True, uses maximum compression quality
    
    Returns:
        Compressed image as bytes in PNG format
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    
    if hd_quality:
        # HD mode: Use high compression level (9) for best quality/size ratio
        buffer = BytesIO()
        image.save(buffer, format='PNG', compress_level=9, optimize=True)
        return buffer.getvalue()
    
    # Standard mode: Try different compression levels
    for compress_level in range(9, -1, -1):
        buffer = BytesIO()
        image.save(buffer, format='PNG', compress_level=compress_level, optimize=True)
        size = buffer.tell()
        
        if size <= max_size_bytes:
            return buffer.getvalue()
    
    # If still too large, return best effort
    return buffer.getvalue()
