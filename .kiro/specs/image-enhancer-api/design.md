# Design Document: AI Image Enhancer API

## Overview

The AI Image Enhancer API is a FastAPI-based microservice that provides image upscaling and compression capabilities through a RESTful HTTP interface. The system accepts image uploads, validates them, upscales them by 2x using high-quality LANCZOS resampling, and returns optimized WEBP images compressed to under 1MB.

The architecture follows a modular design with clear separation of concerns:
- **Validation Layer**: Ensures uploaded files meet size, type, and integrity requirements
- **Processing Layer**: Handles image upscaling with quality preservation
- **Compression Layer**: Optimizes output size through iterative quality reduction
- **API Layer**: Manages HTTP request/response lifecycle and error handling

All processing occurs in-memory using BytesIO streams, making the service stateless and horizontally scalable. The design prioritizes production readiness with comprehensive error handling, security measures, and deployment configuration for Render.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI App                          │
│                         (main.py)                            │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├──► Validator (validators.py)
                │    - File size validation
                │    - MIME type validation
                │    - Image integrity validation
                │
                ├──► Image Processor (enhancer.py)
                │    - RGB conversion
                │    - 2x upscaling with LANCZOS
                │    - Aspect ratio preservation
                │
                └──► Compressor (compressor.py)
                     - WEBP conversion
                     - Iterative quality reduction
                     - Size optimization to ≤1MB
```

### Request Flow

1. **Request Reception**: FastAPI receives POST /enhance with multipart/form-data
2. **Validation Phase**: 
   - Check file size ≤ 5MB
   - Verify MIME type (image/jpeg, image/png, image/webp)
   - Attempt to open with Pillow to confirm valid image
3. **Processing Phase**:
   - Load image into memory using BytesIO
   - Convert to RGB if necessary
   - Upscale to 2x dimensions using LANCZOS
4. **Compression Phase**:
   - Convert to WEBP format
   - Iteratively reduce quality (95 → 90 → 85...) until size ≤ 1MB
   - Stop at quality 10 minimum
5. **Response Delivery**: Return StreamingResponse with WEBP image

### Technology Stack

- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **Uvicorn**: ASGI server for production deployment
- **Pillow (PIL)**: Image processing library for upscaling and format conversion
- **python-multipart**: Multipart form data parsing for file uploads
- **BytesIO**: In-memory binary streams for stateless processing

## Components and Interfaces

### 1. Main Application (app/main.py)

**Responsibilities**:
- Initialize FastAPI application
- Configure CORS middleware
- Define API endpoints
- Orchestrate validation, processing, and compression
- Handle errors and return appropriate HTTP responses

**Key Endpoints**:

```python
POST /enhance
- Request: multipart/form-data with "file" field
- Returns: StreamingResponse with WEBP image
- Status Codes:
  - 200: Success
  - 400: Invalid file type
  - 413: File too large
  - 422: Corrupted image
  - 500: Internal server error

GET /health
- Returns: {"status": "healthy"}
- Status Code: 200
```

**Configuration**:
- Max request body size: 6MB (slightly above 5MB limit for headers)
- CORS: Configurable allowed origins
- Logging: Structured logging for debugging

### 2. Validator Module (app/validators.py)

**Responsibilities**:
- Validate file size before processing
- Verify MIME type against allowed list
- Confirm image can be opened by Pillow
- Raise HTTPException with appropriate status codes

**Interface**:

```python
def validate_file_size(file: UploadFile, max_size_mb: int = 5) -> None:
    """
    Validates that uploaded file does not exceed maximum size.
    Raises HTTPException(413) if file is too large.
    """

def validate_mime_type(file: UploadFile, allowed_types: list[str]) -> None:
    """
    Validates that file MIME type is in allowed list.
    Raises HTTPException(400) if type is not allowed.
    """

def validate_image_integrity(image_bytes: bytes) -> Image.Image:
    """
    Attempts to open image with Pillow to verify it's valid.
    Returns opened Image object.
    Raises HTTPException(422) if image is corrupted.
    """
```

**Validation Logic**:
- File size checked via `file.size` or by reading content length
- MIME type checked via `file.content_type`
- Image integrity verified by `Image.open()` with exception handling

### 3. Image Processor Module (app/enhancer.py)

**Responsibilities**:
- Convert images to RGB color mode
- Upscale images by exactly 2x using LANCZOS resampling
- Maintain aspect ratio (implicit in 2x scaling)
- Return processed image in memory

**Interface**:

```python
def upscale_image(image: Image.Image, scale_factor: int = 2) -> Image.Image:
    """
    Upscales image by the specified factor using LANCZOS resampling.
    Converts to RGB if necessary.
    Returns upscaled Image object.
    """
```

**Processing Logic**:
1. Check if image mode is RGB; if not, convert using `image.convert('RGB')`
2. Calculate new dimensions: `(width * scale_factor, height * scale_factor)`
3. Use `image.resize(new_size, Image.LANCZOS)` for high-quality upscaling
4. Return upscaled image

**Note**: LANCZOS (also called Lanczos3) is a high-quality resampling filter that produces sharp results with minimal artifacts, ideal for upscaling.

### 4. Compressor Module (app/compressor.py)

**Responsibilities**:
- Convert images to WEBP format
- Iteratively reduce quality until size ≤ 1MB
- Return compressed image as bytes

**Interface**:

```python
def compress_to_webp(image: Image.Image, max_size_mb: float = 1.0) -> bytes:
    """
    Compresses image to WEBP format with size constraint.
    Iteratively reduces quality from 95 to 10 until size ≤ max_size_mb.
    Returns compressed image as bytes.
    """
```

**Compression Algorithm**:
```
quality = 95
max_size_bytes = max_size_mb * 1024 * 1024

while quality >= 10:
    buffer = BytesIO()
    image.save(buffer, format='WEBP', quality=quality)
    size = buffer.tell()
    
    if size <= max_size_bytes:
        return buffer.getvalue()
    
    quality -= 5

# If still too large at quality 10, return best effort
return buffer.getvalue()
```

**Optimization Strategy**:
- Start at quality 95 for minimal quality loss
- Reduce by 5 each iteration for reasonable convergence speed
- Stop at quality 10 to prevent excessive degradation
- WEBP format chosen for superior compression vs JPEG/PNG

## Data Models

### UploadFile (FastAPI)

```python
class UploadFile:
    filename: str           # Original filename
    content_type: str       # MIME type (e.g., "image/jpeg")
    file: SpooledTemporaryFile  # File-like object
    size: int              # File size in bytes (if available)
```

### Image (Pillow)

```python
class Image:
    size: tuple[int, int]   # (width, height)
    mode: str               # Color mode (e.g., "RGB", "RGBA", "L")
    format: str             # Original format (e.g., "JPEG", "PNG")
```

### Response Models

```python
# Success: StreamingResponse with image bytes
# Content-Type: image/webp
# Content-Disposition: attachment; filename="enhanced.webp"

# Error responses (JSON):
{
    "detail": "Error message"
}
```

## Error Handling

### Error Categories and Responses

1. **Invalid File Type (400 Bad Request)**
   - Trigger: MIME type not in [image/jpeg, image/png, image/webp]
   - Response: `{"detail": "Invalid file type. Allowed types: JPEG, PNG, WEBP"}`

2. **File Too Large (413 Payload Too Large)**
   - Trigger: File size > 5MB
   - Response: `{"detail": "File size exceeds 5MB limit"}`

3. **Corrupted Image (422 Unprocessable Entity)**
   - Trigger: Pillow cannot open the file
   - Response: `{"detail": "Unable to process image. File may be corrupted"}`

4. **Internal Server Error (500)**
   - Trigger: Unexpected exceptions during processing
   - Response: `{"detail": "Internal server error occurred"}`
   - Note: Stack traces logged but not exposed to client

### Exception Handling Strategy

```python
try:
    # Validation
    validate_file_size(file)
    validate_mime_type(file)
    
    # Read and validate image
    image_bytes = await file.read()
    image = validate_image_integrity(image_bytes)
    
    # Process
    upscaled = upscale_image(image)
    compressed = compress_to_webp(upscaled)
    
    # Return response
    return StreamingResponse(BytesIO(compressed), media_type="image/webp")
    
except HTTPException:
    raise  # Re-raise HTTP exceptions as-is
    
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error occurred")
```

### Security Considerations

- **CORS Configuration**: Restrict allowed origins in production
- **File Size Limits**: Enforce at application level (5MB) and server level (6MB)
- **MIME Type Validation**: Prevent execution of non-image files
- **Image Integrity Check**: Prevent malicious file uploads disguised as images
- **Memory Management**: Use BytesIO to prevent disk-based attacks
- **Error Message Sanitization**: Never expose internal paths or stack traces

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases for each module:

**Validator Tests**:
- Test file size validation with files at boundary (exactly 5MB, 5MB + 1 byte)
- Test MIME type validation with allowed and disallowed types
- Test image integrity with valid images and corrupted files
- Test error messages and status codes

**Enhancer Tests**:
- Test upscaling with various image sizes
- Test RGB conversion from RGBA, grayscale, and other modes
- Test that dimensions are exactly 2x original
- Test with minimum size images (1x1 pixel)

**Compressor Tests**:
- Test compression with images that compress easily (solid colors)
- Test compression with images that compress poorly (high detail)
- Test that output is always ≤ 1MB (or best effort at quality 10)
- Test WEBP format output

**Integration Tests**:
- Test complete flow from upload to response
- Test error handling at each stage
- Test concurrent requests
- Test memory cleanup after processing

### Property-Based Testing

Property-based tests will verify universal correctness properties across many generated inputs. Each property test will run a minimum of 100 iterations with randomized inputs.


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: File Upload Acceptance

*For any* valid image file (JPEG, PNG, or WEBP) under 5MB, when posted to /enhance with field name "file", the API should accept and process the file without validation errors.

**Validates: Requirements 1.1**

### Property 2: File Validation Rejection

*For any* uploaded file, if it exceeds 5MB, has an invalid MIME type (not image/jpeg, image/png, or image/webp), or is corrupted, the API should reject it with the appropriate HTTP status code (413 for size, 400 for type, 422 for corruption) and return a clear error message.

**Validates: Requirements 1.2, 1.3, 1.4**

### Property 3: Upscaling Dimensions

*For any* valid input image with dimensions (W, H), after upscaling, the output image should have dimensions (2W, 2H).

**Validates: Requirements 2.1**

### Property 4: RGB Conversion

*For any* input image in non-RGB color mode (RGBA, grayscale, CMYK, etc.), the upscaled output image should be in RGB mode.

**Validates: Requirements 2.3**

### Property 5: WEBP Format Output

*For any* successfully processed image, the output should be in WEBP format.

**Validates: Requirements 3.1**

### Property 6: Size Constraint

*For any* image that can be compressed to 1MB or less at quality ≥ 10, the compressed output should have a file size at or below 1MB.

**Validates: Requirements 3.4**

### Property 7: Response Type and Headers

*For any* successfully processed image, the API should return a StreamingResponse with Content-Type "image/webp" and an appropriate Content-Disposition header.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 8: Error Response Format

*For any* processing failure (validation error, processing exception), the API should return an appropriate HTTP error status code with a JSON error message that does not expose internal stack traces.

**Validates: Requirements 4.4, 6.1, 6.2**

### Property 9: Request Size Limit

*For any* HTTP request exceeding the configured maximum body size (6MB), the API should reject the request before processing.

**Validates: Requirements 6.4**

### Property 10: Upscaling Round-Trip Dimensions

*For any* valid image, if we record its dimensions, upscale it, then check the upscaled dimensions, the ratio of (upscaled_width / original_width) should equal 2.0 and (upscaled_height / original_height) should equal 2.0.

**Validates: Requirements 2.1**

**Note**: This is a round-trip property that verifies the mathematical relationship between input and output dimensions.

## Deployment Configuration

### Project Structure

```
image-enhancer-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and endpoints
│   ├── enhancer.py      # Image upscaling logic
│   ├── compressor.py    # Image compression logic
│   └── validators.py    # File validation logic
├── tests/
│   ├── __init__.py
│   ├── test_validators.py
│   ├── test_enhancer.py
│   ├── test_compressor.py
│   └── test_integration.py
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment configuration
├── .env.example        # Environment variable template
└── README.md           # Project documentation
```

### Dependencies (requirements.txt)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pillow==10.1.0
python-multipart==0.0.6
```

### Render Configuration (render.yaml)

```yaml
services:
  - type: web
    name: image-enhancer-api
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 10000
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: MAX_UPLOAD_SIZE_MB
        value: 5
      - key: MAX_OUTPUT_SIZE_MB
        value: 1
```

### Environment Variables

- `MAX_UPLOAD_SIZE_MB`: Maximum upload file size (default: 5)
- `MAX_OUTPUT_SIZE_MB`: Maximum output file size (default: 1)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (default: "*")
- `LOG_LEVEL`: Logging level (default: "INFO")

### Performance Considerations

**Memory Usage**:
- Peak memory per request: ~3x largest image size (original + upscaled + compressed)
- 5MB upload → ~15MB peak memory per request
- Recommend at least 512MB RAM for production

**Processing Time**:
- Typical 2MB image: 1-3 seconds
- Factors: original size, complexity, compression iterations
- Upscaling is CPU-intensive; consider CPU-optimized instances

**Concurrency**:
- Uvicorn workers can be configured for parallel request handling
- Each worker handles requests sequentially
- For high traffic, use multiple workers: `--workers 4`

### Monitoring and Observability

**Health Check**:
- Endpoint: GET /health
- Use for Render health checks and load balancer probes
- Returns: `{"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}`

**Logging**:
- Structured JSON logs for production
- Log levels: DEBUG, INFO, WARNING, ERROR
- Key events logged:
  - Request received with file size
  - Validation failures with reason
  - Processing start/complete with timing
  - Errors with sanitized details

**Metrics to Monitor**:
- Request rate and latency
- Error rate by status code
- Memory usage per request
- CPU utilization during processing
- Response size distribution

## Security Hardening

### Input Validation
- Strict MIME type checking
- File size limits enforced at multiple layers
- Image integrity verification before processing
- Reject files with suspicious extensions

### Resource Protection
- Request body size limits prevent memory exhaustion
- Processing timeout prevents CPU exhaustion
- In-memory processing prevents disk space attacks
- No file persistence reduces attack surface

### CORS Configuration
```python
# Production: Restrict to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### Error Handling
- Never expose internal paths or stack traces
- Sanitize all error messages
- Log detailed errors server-side only
- Return generic 500 errors for unexpected exceptions

### Rate Limiting (Recommended)
- Consider adding rate limiting middleware
- Limit requests per IP address
- Prevent abuse and DoS attacks
- Example: slowapi or fastapi-limiter

## Testing Strategy

### Unit Testing Approach

Unit tests will verify specific behaviors and edge cases for each module using pytest:

**Validator Module Tests**:
- Test file size validation at boundaries (4.9MB, 5MB, 5.1MB)
- Test each allowed MIME type (image/jpeg, image/png, image/webp)
- Test rejected MIME types (image/gif, application/pdf, text/plain)
- Test corrupted image data (truncated files, invalid headers)
- Test error messages match expected format
- Test HTTP status codes (400, 413, 422)

**Enhancer Module Tests**:
- Test upscaling with various dimensions (100x100, 1920x1080, 1x1)
- Test RGB conversion from RGBA, L (grayscale), P (palette), CMYK
- Test that output dimensions are exactly 2x input
- Test with minimum size images (1x1 pixel)
- Test with maximum practical size images
- Test aspect ratio preservation

**Compressor Module Tests**:
- Test compression with simple images (solid colors) that compress easily
- Test compression with complex images (high detail) that compress poorly
- Test that output is WEBP format
- Test that output size ≤ 1MB when achievable
- Test minimum quality threshold (quality 10)
- Test with images that cannot compress below 1MB

**Integration Tests**:
- Test complete flow: upload → validate → upscale → compress → respond
- Test error handling at each stage
- Test concurrent requests (simulate multiple clients)
- Test memory cleanup (no memory leaks)
- Test response headers and content type
- Test health endpoint

### Property-Based Testing Approach

Property-based tests will use **Hypothesis** (Python's leading PBT library) to verify universal correctness properties across many generated inputs. Each property test will run a minimum of 100 iterations with randomized inputs.

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(image=st_valid_images())
def test_property(image):
    # Test implementation
    pass
```

**Custom Strategies**:
- `st_valid_images()`: Generate random valid images (various sizes, formats, modes)
- `st_invalid_mime_types()`: Generate non-image MIME types
- `st_large_files()`: Generate files exceeding size limits
- `st_corrupted_images()`: Generate corrupted image data

**Property Test Implementation**:

Each correctness property from the design will be implemented as a property-based test:

1. **Property 1: File Upload Acceptance**
   - Generate random valid images under 5MB
   - Post to /enhance endpoint
   - Assert: No validation errors, processing succeeds
   - Tag: `# Feature: image-enhancer-api, Property 1: File Upload Acceptance`

2. **Property 2: File Validation Rejection**
   - Generate files with various invalid conditions
   - Post to /enhance endpoint
   - Assert: Correct status code (413/400/422) and error message
   - Tag: `# Feature: image-enhancer-api, Property 2: File Validation Rejection`

3. **Property 3: Upscaling Dimensions**
   - Generate random images with various dimensions
   - Upscale using enhancer module
   - Assert: output dimensions = 2 × input dimensions
   - Tag: `# Feature: image-enhancer-api, Property 3: Upscaling Dimensions`

4. **Property 4: RGB Conversion**
   - Generate images in various color modes (RGBA, L, P, CMYK)
   - Upscale using enhancer module
   - Assert: output mode = "RGB"
   - Tag: `# Feature: image-enhancer-api, Property 4: RGB Conversion`

5. **Property 5: WEBP Format Output**
   - Generate random valid images
   - Process through complete pipeline
   - Assert: output format is WEBP
   - Tag: `# Feature: image-enhancer-api, Property 5: WEBP Format Output`

6. **Property 6: Size Constraint**
   - Generate images that can compress to ≤1MB
   - Compress using compressor module
   - Assert: output size ≤ 1MB
   - Tag: `# Feature: image-enhancer-api, Property 6: Size Constraint`

7. **Property 7: Response Type and Headers**
   - Generate random valid images
   - Post to /enhance endpoint
   - Assert: StreamingResponse with correct Content-Type and Content-Disposition
   - Tag: `# Feature: image-enhancer-api, Property 7: Response Type and Headers`

8. **Property 8: Error Response Format**
   - Generate various error conditions
   - Trigger errors through API
   - Assert: Appropriate status code, JSON error, no stack traces
   - Tag: `# Feature: image-enhancer-api, Property 8: Error Response Format`

9. **Property 9: Request Size Limit**
   - Generate requests exceeding max body size
   - Post to /enhance endpoint
   - Assert: Request rejected before processing
   - Tag: `# Feature: image-enhancer-api, Property 9: Request Size Limit`

10. **Property 10: Upscaling Round-Trip Dimensions**
    - Generate random images
    - Record dimensions, upscale, measure output
    - Assert: width_ratio = 2.0 and height_ratio = 2.0
    - Tag: `# Feature: image-enhancer-api, Property 10: Upscaling Round-Trip Dimensions`

**Test Execution**:
```bash
# Run all tests
pytest tests/ -v

# Run only property tests
pytest tests/ -v -m property

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Complementary Testing Strategy

Unit tests and property tests work together to provide comprehensive coverage:

- **Unit tests** catch specific bugs, edge cases, and integration issues
- **Property tests** verify universal correctness across many inputs
- **Together** they ensure both concrete examples work and general properties hold

This dual approach catches both specific regressions and general correctness violations, providing confidence in the system's reliability.
