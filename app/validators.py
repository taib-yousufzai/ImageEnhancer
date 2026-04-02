"""
File validation module for image upload validation.

This module provides validation functions for uploaded files including:
- File size validation
- MIME type validation
- Image integrity validation
"""

from fastapi import UploadFile, HTTPException
from PIL import Image
from io import BytesIO

# Prevent decompression bomb DOS attacks explicitly (~90 Megapixels ceiling)
Image.MAX_IMAGE_PIXELS = 89478485


def validate_file_size(file: UploadFile, max_size_mb: float = 5.0) -> None:
    """
    Validate file size is within acceptable limits.
    
    Args:
        file: File upload object
        max_size_mb: Maximum allowed file size in MB (default: 5MB)
    
    Raises:
        HTTPException: 413 if file exceeds size limit
    
    Requirements:
        - 1.2: Enforce 5MB max size
    """
    # Check content-length header if available
    if file.size and file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )


def validate_mime_type(
    file: UploadFile,
    allowed_types: list[str] = None
) -> None:
    """
    Validates that file MIME type is in allowed list.
    
    Args:
        file: The uploaded file to validate
        allowed_types: List of allowed MIME types (default: image/jpeg, image/png, image/webp)
    
    Raises:
        HTTPException: 400 status if MIME type is not allowed
    """
    if allowed_types is None:
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
    
    if file.content_type not in allowed_types:
        allowed_str = ", ".join([t.split("/")[1].upper() for t in allowed_types])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {allowed_str}"
        )


def validate_image_integrity(image_bytes: bytes) -> Image.Image:
    """
    Attempts to open image with Pillow to verify it's valid.
    
    Args:
        image_bytes: The image data as bytes
    
    Returns:
        Image.Image: The opened PIL Image object
    
    Raises:
        HTTPException: 422 status if image is corrupted or cannot be opened
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        # Verify the image by loading it
        image.verify()
        # Reopen since verify() closes the file
        image = Image.open(BytesIO(image_bytes))
        return image
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail="Unable to process image. File may be corrupted"
        )
