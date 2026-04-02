# AI Image Enhancer

A full-stack application for enhancing images with AI-powered upscaling and compression. The frontend is built with Next.js 14, TypeScript, and Tailwind CSS, while the backend API is powered by FastAPI and Pillow for high-quality image processing.

## Features

### Frontend
- Drag-and-drop or click-to-upload image selection
- Real-time image preview
- AI-powered image enhancement via backend API
- Download enhanced images
- Responsive design for mobile, tablet, and desktop
- Clean, modern SaaS-style interface

### Backend API
- Image upscaling by 2x using high-quality LANCZOS resampling
- Automatic compression to WEBP format (≤1MB)
- Support for JPEG, PNG, and WEBP input formats
- File validation (size, type, integrity)
- In-memory processing for scalability
- RESTful API with automatic OpenAPI documentation

## Getting Started

### Prerequisites

- Node.js 18+ installed (for frontend)
- Python 3.10+ installed (for backend)
- npm or yarn package manager

### Backend Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file (optional, uses defaults if not provided):

```bash
cp .env.example .env
```

3. Run the backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation is automatically available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

3. Create a `.env.local` file in the root directory:

```bash
cp .env.example .env.local
```

4. Update the `NEXT_PUBLIC_API_URL` in `.env.local` with your backend API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/enhance
```

For production, use your deployed backend URL.

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

Build the application for production:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Backend API Documentation

### Endpoints

#### POST /enhance

Upscales an image by 2x and compresses it to WEBP format.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form field `file` containing the image file

**Constraints:**
- Maximum file size: 5MB
- Allowed formats: JPEG, PNG, WEBP
- File must be a valid, non-corrupted image

**Response:**
- Success (200): Returns the enhanced image as `image/webp`
- Error (400): Invalid file type
- Error (413): File too large (>5MB)
- Error (422): Corrupted or invalid image
- Error (500): Internal server error

**Example using curl:**

```bash
curl -X POST http://localhost:8000/enhance \
  -F "file=@/path/to/image.jpg" \
  -o enhanced.webp
```

**Example using Python:**

```python
import requests

url = "http://localhost:8000/enhance"
files = {"file": open("image.jpg", "rb")}
response = requests.post(url, files=files)

if response.status_code == 200:
    with open("enhanced.webp", "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.json()}")
```

**Example using JavaScript:**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/enhance', {
  method: 'POST',
  body: formData
});

if (response.ok) {
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  // Use the URL to display or download the image
} else {
  const error = await response.json();
  console.error('Error:', error.detail);
}
```

#### GET /health

Health check endpoint for monitoring.

**Request:**
- Method: `GET`

**Response:**
- Success (200): `{"status": "healthy"}`

**Example:**

```bash
curl http://localhost:8000/health
```

### Image Processing Details

1. **Validation**: Checks file size (≤5MB), MIME type, and image integrity
2. **Upscaling**: Uses LANCZOS resampling to upscale by 2x (doubles width and height)
3. **RGB Conversion**: Converts images to RGB mode if necessary
4. **Compression**: Iteratively compresses to WEBP format, targeting ≤1MB file size
5. **Quality Optimization**: Starts at quality 95, reduces by 5 until size ≤1MB or quality reaches 10

### Environment Variables

Backend environment variables (optional, with defaults):

- `MAX_UPLOAD_SIZE_MB`: Maximum upload file size in MB (default: 5)
- `MAX_OUTPUT_SIZE_MB`: Target output file size in MB (default: 1)
- `ALLOWED_ORIGINS`: CORS allowed origins, comma-separated (default: "*")
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: "INFO")

## Deployment

### Backend Deployment (Render)

The backend is configured for deployment on Render using the included `render.yaml` file.

**Automatic Deployment:**

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Connect your repository to [Render](https://render.com)
3. Render will automatically detect the `render.yaml` configuration
4. The service will be deployed with the specified environment variables

**Manual Deployment:**

1. Create a new Web Service on Render
2. Connect your repository
3. Configure the service:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
   - **Python Version**: 3.10.0
4. Add environment variables as needed
5. Deploy!

The API will be available at your Render service URL (e.g., `https://your-service.onrender.com`)

**Performance Recommendations:**
- Minimum 512MB RAM for production workloads
- Consider CPU-optimized instances for faster image processing
- Use multiple workers for high traffic: `--workers 4` in start command

### Frontend Deployment (Vercel)

This application is optimized for deployment on Vercel:

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Import your repository in [Vercel](https://vercel.com)
3. Add the `NEXT_PUBLIC_API_URL` environment variable in Vercel project settings
4. Deploy!

Vercel will automatically detect Next.js and configure the build settings.

### Other Platforms

**Frontend** can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway

**Backend** can be deployed to any platform that supports Python/FastAPI:
- Railway
- Fly.io
- AWS Elastic Beanstalk
- Google Cloud Run
- Heroku

Make sure to:
- Set appropriate build and start commands
- Configure environment variables for both frontend and backend
- Update CORS settings in production for security

## Environment Variables

### Frontend
- `NEXT_PUBLIC_API_URL`: The URL of your backend image enhancement API endpoint

### Backend
- `MAX_UPLOAD_SIZE_MB`: Maximum upload file size in MB (default: 5)
- `MAX_OUTPUT_SIZE_MB`: Target output file size in MB (default: 1)
- `ALLOWED_ORIGINS`: CORS allowed origins, comma-separated (default: "*")
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: "INFO")

## Project Structure

### Frontend
```
app/
  page.tsx              # Main application page
  layout.tsx            # Root layout with metadata
  globals.css           # Global styles
components/
  UploadCard.tsx        # Main upload and enhancement UI
  Loader.tsx            # Loading indicator component
lib/
  api.ts                # API integration layer
  types.ts              # TypeScript type definitions
  validation.ts         # File validation utilities
  utils.ts              # Utility functions
```

### Backend
```
app/
  __init__.py           # Python package initialization
  main.py               # FastAPI application and endpoints
  enhancer.py           # Image upscaling logic (LANCZOS)
  compressor.py         # Image compression logic (WEBP)
  validators.py         # File validation (size, type, integrity)
tests/
  __init__.py           # Test package initialization
  test_integration.py   # Integration tests
  test_smoke.py         # Smoke tests
requirements.txt        # Python dependencies
render.yaml             # Render deployment configuration
```

## Technologies

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks (useState, useEffect)

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Image Processing**: Pillow (PIL)
- **Server**: Uvicorn (ASGI)
- **Testing**: pytest, hypothesis

## Testing

### Backend Tests

Run the backend test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_integration.py -v
```

The test suite includes:
- Unit tests for validators, enhancer, and compressor modules
- Integration tests for the complete API flow
- Property-based tests using Hypothesis for correctness verification

## License

MIT
#   I m a g e E n h a n c e r  
 