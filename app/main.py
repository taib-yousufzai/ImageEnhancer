"""
AI Image Enhancer API - FastAPI application.

This module provides the main FastAPI application with endpoints for:
- Image enhancement (upload, validate, upscale, compress)
- Health check monitoring
"""

import logging
from datetime import datetime
from io import BytesIO
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Security, Request, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.validators import validate_file_size, validate_mime_type, validate_image_integrity
from app.enhancer import upscale_image
from app.compressor import compress_to_webp
from app.auth import verify_api_key

def get_identifier(request: Request) -> str:
    """Extract API key for rate limiting, fallback to IP if unauthenticated."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return get_remote_address(request)

limiter = Limiter(key_func=get_identifier)

from app.validators import validate_file_size, validate_mime_type, validate_image_integrity
from app.enhancer import upscale_image
from app.compressor import compress_to_webp


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="AI Image Enhancer API",
    description="A production-ready API for upscaling and compressing images",
    version="1.0.0"
)

# Apply Rate Limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS middleware using environment variable
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task storage & Capacity limits
TASKS = {}
TASK_TTL_SECONDS = 3600 # 1 hour
MAX_CONCURRENT_TASKS = int(os.environ.get("MAX_CONCURRENT_TASKS", "50"))

async def cleanup_tasks_loop():
    """Background loop to periodically clear old tasks and free memory."""
    import asyncio
    import time
    
    logger.info("Task cleanup service started")
    while True:
        try:
            await asyncio.sleep(600) # Run every 10 minutes
            now = time.time()
            expired_ids = []
            
            # Identify tasks older than TTL
            for tid, data in TASKS.items():
                start_time = data.get("start_time")
                # Clean up if older than TTL or if completed/failed and 15 mins passed
                is_old = start_time and (now - start_time > TASK_TTL_SECONDS)
                is_finished = data["status"] in ["completed", "failed"]
                
                if is_old or (is_finished and start_time and (now - start_time > 1800)):
                    expired_ids.append(tid)
            
            if expired_ids:
                logger.info(f"[CLEANUP] Removing {len(expired_ids)} stale tasks")
                for tid in expired_ids:
                    # Explicitly delete large binary result if it exists before removing entry
                    if "result" in TASKS[tid]:
                        del TASKS[tid]["result"]
                    del TASKS[tid]
                
                # Force garbage collection after clearing large binary data
                import gc
                gc.collect()
                
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(cleanup_tasks_loop())


def process_enhancement_task(task_id: str, file_bytes: bytes, output_format: str, scale: int, width: int | None, height: int | None, ultra_mode: bool):
    """Background task to process image enhancement with progress tracking."""
    import time
    start_time = time.time()
    
    logger.info(f"[TASK START] Task {task_id} starting execution")
    # Typical durations for initial estimation (conservative CPU speeds)
    if ultra_mode:
        expected_total = 45.0
    elif scale > 2 or (width and width > 1500): # heuristic for x4 model
        expected_total = 20.0
    else:
        expected_total = 8.0

    try:
        TASKS[task_id] = {
            "status": "processing", 
            "progress": 0, 
            "message": "Starting...",
            "start_time": start_time,
            "estimated_time_remaining": round(expected_total, 1)
        }
        logger.info(f"[TASK] Created task entry for {task_id}")

        def update_progress(progress, message):
            TASKS[task_id]["progress"] = progress
            TASKS[task_id]["message"] = message
            
            elapsed = time.time() - start_time
            if progress > 0:
                # Calculate what the total time would be if current speed holds
                live_estimated_total = (elapsed / progress) * 100
                
                # Blend the "typical" expectation with live data
                # Early on (0-20%), we lean on the typical expectation
                # Later on (20%+), we trust the live data more
                blend_factor = min(1.0, progress / 20.0) 
                total_estimated = (expected_total * (1 - blend_factor)) + (live_estimated_total * blend_factor)
                
                remaining = max(1, total_estimated - elapsed)
                TASKS[task_id]["estimated_time_remaining"] = round(remaining, 1)
            else:
                # Very start, provide the best guess
                TASKS[task_id]["estimated_time_remaining"] = round(expected_total, 1)
            
            logger.info(f"[TASK PROGRESS] {task_id}: {progress}% - {message} (ETA: {TASKS[task_id]['estimated_time_remaining']}s)")
            
        # Validate image integrity and open
        logger.info(f"[TASK] Validating image for {task_id}")
        image = validate_image_integrity(file_bytes)
        
        logger.info(f"Task {task_id}: Processing image, scale: {scale}x, width: {width}, height: {height}, ultra: {ultra_mode}")
        
        # Processing phase with callback
        upscaled = upscale_image(
            image, 
            scale_factor=scale, 
            target_width=width, 
            target_height=height, 
            ultra_mode=ultra_mode,
            progress_callback=update_progress
        )
        
        TASKS[task_id]["message"] = "Compressing..."
        
        # Compression phase
        if output_format == "webp":
            compressed = compress_to_webp(upscaled, max_size_mb=10.0, hd_quality=True)
            media_type = "image/webp"
            extension = "webp"
        elif output_format == "jpeg":
            from app.compressor import compress_to_jpeg
            compressed = compress_to_jpeg(upscaled, max_size_mb=10.0, hd_quality=True)
            media_type = "image/jpeg"
            extension = "jpg"
        else:  # png
            from app.compressor import compress_to_png
            compressed = compress_to_png(upscaled, max_size_mb=10.0, hd_quality=True)
            media_type = "image/png"
            extension = "png"
            
        TASKS[task_id]["result"] = compressed
        TASKS[task_id]["media_type"] = media_type
        TASKS[task_id]["extension"] = extension
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 100
        TASKS[task_id]["message"] = "Completed"
        
        logger.info(f"Task {task_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {str(e)}", exc_info=True)
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)


@app.post("/enhance")
@limiter.limit("5/minute")
async def enhance_image_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = "webp",
    scale: int = 2,
    width: int | None = None,
    height: int | None = None,
    ultra_mode: bool = False,
    api_key: str = Security(verify_api_key)
):
    """
    Start an asynchronous image enhancement task.
    Requires valid API key. Uses Rate Limiting explicitly against the API key.
    """
    # Validate file type first
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate Output & Scale
    output_format = output_format.lower()
    allowed_formats = ["webp", "jpeg", "png"]
    if output_format not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format. Allowed: {allowed_formats}")
            
    if not width and not height and scale not in [1, 2, 4]:
         raise HTTPException(status_code=400, detail="Invalid scale. Allowed: 1, 2, 4")
         
    if len(TASKS) >= MAX_CONCURRENT_TASKS:
         logger.warning("[ENDPOINT] Rejected request due to max concurrent tasks exceeded.")
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server at maximum capacity. Try again later.")
    
    try:
        # Validate metadata limits prior to reading into a massive contiguous bytes object
        validate_file_size(file)
        validate_mime_type(file)
        
        # Read bytes
        file_bytes = await file.read()
        
        # Generate ID
        task_id = str(uuid.uuid4())
        logger.info(f"[ENDPOINT] Generated task_id: {task_id}")
        
        # Pre-initialize task state to avoid 404 during polling
        TASKS[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Initialising...",
            "estimated_time_remaining": None
        }
        
        # Start background task
        logger.info(f"[ENDPOINT] Adding task {task_id} to background queue")
        background_tasks.add_task(
            process_enhancement_task, 
            task_id, 
            file_bytes, 
            output_format, 
            scale, 
            width, 
            height, 
            ultra_mode
        )
        logger.info(f"[ENDPOINT] Task {task_id} added successfully")
        
        return {"task_id": task_id}
        
    except Exception as e:
        logger.error(f"[ENDPOINT] Error starting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        

@app.post("/enhance-batch")
@limiter.limit("2/minute")
async def enhance_batch_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    output_format: str = "webp",
    scale: int = 2,
    width: int | None = None,
    height: int | None = None,
    ultra_mode: bool = False,
    api_key: str = Security(verify_api_key)
):
    """
    Start multiple asynchronous image enhancement tasks.
    Requires secure API key token. Severely rate limited to prevent pipeline overload.
    """
    task_ids = []
    errors = []

    for file in files:
        try:
            filename = file.filename or "unknown"
            
            # Validation Before Read
            try:
                validate_file_size(file)
                validate_mime_type(file)
                
                if len(TASKS) >= MAX_CONCURRENT_TASKS:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server capacity reached.")
                    
            except HTTPException as he:
                errors.append({"filename": filename, "error": he.detail})
                continue
                
            # Read bytes carefully
            file_bytes = await file.read()
            
            # Generate ID
            task_id = str(uuid.uuid4())
            
            # Pre-initialize task state
            TASKS[task_id] = {
                "status": "processing",
                "progress": 0,
                "message": "Queued",
                "estimated_time_remaining": None
            }
            
            # Start background task
            background_tasks.add_task(
                process_enhancement_task, 
                task_id, 
                file_bytes, 
                output_format, 
                scale, 
                width, 
                height, 
                ultra_mode
            )
            
            task_ids.append({"filename": filename, "task_id": task_id})
            
        except Exception as e:
            logger.error(f"Error starting task for {getattr(file, 'filename', 'unknown')}: {e}")
            errors.append({"filename": getattr(file, "filename", "unknown"), "error": str(e)})

    return {"tasks": task_ids, "errors": errors}


@app.get("/status/{task_id}")
@limiter.limit("60/minute")
async def get_task_status(request: Request, task_id: str):
    """Get the status of an enhancement task."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = TASKS[task_id]
    return {
        "status": task["status"],
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "estimated_time_remaining": task.get("estimated_time_remaining"),
        "error": task.get("error")
    }


@app.get("/result/{task_id}")
@limiter.limit("30/minute")
async def get_task_result(request: Request, task_id: str):
    """Retrieve the result of a completed task."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task = TASKS[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
        
    # Send headers to prevent browser sniffing and caching
    return StreamingResponse(
        BytesIO(task["result"]),
        media_type=task["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="enhanced.{task["extension"]}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, max-age=0",
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.
    
    Returns:
        JSON with status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
