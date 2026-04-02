"""
Integration tests for the complete API flow.
Tests the /enhance and /health endpoints.
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_enhance_endpoint_with_valid_image():
    """Test the enhance endpoint with a valid image."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Upload the image
    files = {"file": ("test.png", buffer, "image/png")}
    response = client.post("/enhance", files=files)
    
    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert "content-disposition" in response.headers
    
    # Verify the response is a valid WEBP image
    result_img = Image.open(BytesIO(response.content))
    assert result_img.format == "WEBP"
    # Original was 100x100, upscaled should be 200x200
    assert result_img.size == (200, 200)


def test_enhance_endpoint_rejects_large_file():
    """Test that the file size validator rejects files over 5MB."""
    from app.validators import validate_file_size
    from unittest.mock import Mock
    
    # Create a mock UploadFile with size > 5MB
    mock_file = Mock()
    mock_file.size = 6 * 1024 * 1024  # 6MB
    
    # Should raise HTTPException with 413
    with pytest.raises(HTTPException) as exc_info:
        validate_file_size(mock_file)
    
    assert exc_info.value.status_code == 413
    assert "5MB" in exc_info.value.detail


def test_enhance_endpoint_rejects_invalid_mime_type():
    """Test that non-image files are rejected."""
    # Create a text file
    text_content = BytesIO(b"This is not an image")
    
    files = {"file": ("test.txt", text_content, "text/plain")}
    response = client.post("/enhance", files=files)
    
    # Should be rejected with 400
    assert response.status_code == 400
    assert "detail" in response.json()


def test_enhance_endpoint_rejects_corrupted_image():
    """Test that corrupted images are rejected."""
    # Create corrupted image data
    corrupted_data = BytesIO(b"PNG\x89\x50\x4E\x47corrupted")
    
    files = {"file": ("corrupted.png", corrupted_data, "image/png")}
    response = client.post("/enhance", files=files)
    
    # Should be rejected with 422
    assert response.status_code == 422
    assert "detail" in response.json()
