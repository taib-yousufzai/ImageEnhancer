"""
Smoke tests to verify core modules can be imported and basic functionality works.
This is a minimal checkpoint test to ensure modules work independently.
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi import UploadFile, HTTPException

from app.validators import validate_file_size, validate_mime_type, validate_image_integrity
from app.enhancer import upscale_image
from app.compressor import compress_to_webp


def test_validators_module_imports():
    """Verify validators module can be imported."""
    assert validate_file_size is not None
    assert validate_mime_type is not None
    assert validate_image_integrity is not None


def test_enhancer_module_imports():
    """Verify enhancer module can be imported."""
    assert upscale_image is not None


def test_compressor_module_imports():
    """Verify compressor module can be imported."""
    assert compress_to_webp is not None


def test_enhancer_basic_functionality():
    """Verify enhancer can upscale a simple image."""
    # Create a simple 10x10 RGB image
    img = Image.new('RGB', (10, 10), color='red')
    
    # Upscale it
    upscaled = upscale_image(img)
    
    # Verify dimensions are 2x
    assert upscaled.size == (20, 20)
    assert upscaled.mode == 'RGB'


def test_compressor_basic_functionality():
    """Verify compressor can compress an image to WEBP."""
    # Create a simple 100x100 RGB image
    img = Image.new('RGB', (100, 100), color='blue')
    
    # Compress it
    compressed_bytes = compress_to_webp(img)
    
    # Verify it's bytes and can be opened as WEBP
    assert isinstance(compressed_bytes, bytes)
    assert len(compressed_bytes) > 0
    
    # Verify it's a valid WEBP image
    result_img = Image.open(BytesIO(compressed_bytes))
    assert result_img.format == 'WEBP'


def test_validator_image_integrity_basic():
    """Verify validator can validate a simple image."""
    # Create a simple image and convert to bytes
    img = Image.new('RGB', (50, 50), color='green')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # Validate it
    validated_img = validate_image_integrity(image_bytes)
    
    # Verify it returns a valid Image object
    assert isinstance(validated_img, Image.Image)
    assert validated_img.size == (50, 50)


def test_validator_image_integrity_rejects_corrupted():
    """Verify validator rejects corrupted image data."""
    corrupted_bytes = b"This is not an image"
    
    with pytest.raises(HTTPException) as exc_info:
        validate_image_integrity(corrupted_bytes)
    
    assert exc_info.value.status_code == 422
