"""
TRELLIS.2 docs-only FastAPI service.

This exposes the same public API shape as trellis2_service.py without loading
the CUDA model stack. Use it when the goal is to inspect /docs or /openapi.json.
"""

import time
import uuid
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
import uvicorn


HOST = "0.0.0.0"
PORT = 9020

app = FastAPI(
    title="TRELLIS.2 Image-to-3D Service (Docs Only)",
    version="1.0.0-docs",
    description=(
        "Docs-only API surface for the TRELLIS.2 image-to-3D service. "
        "It does not load model weights or CUDA extensions."
    ),
)

job_store: dict[str, dict] = {}


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "mode": "docs-only",
        "pipeline_loaded": False,
        "message": "API docs are available; generation runtime is not loaded.",
    }


@app.post("/generate", tags=["generation"])
async def generate(
    image: UploadFile = File(..., description="Reference image used by the real TRELLIS.2 generation service."),
    resolution: Literal[512, 1024, 1536] = Form(512, description="Generation resolution."),
    decimation_target: int = Form(300000, description="Target face count for exported GLB decimation."),
    texture_size: int = Form(2048, description="Texture size for exported GLB."),
) -> dict:
    job_id = uuid.uuid4().hex[:12]
    job_store[job_id] = {
        "job_id": job_id,
        "status": "docs_only",
        "progress": 0,
        "created_at": time.time(),
        "resolution": resolution,
        "decimation_target": decimation_target,
        "texture_size": texture_size,
        "filename": image.filename,
    }
    raise HTTPException(
        status_code=503,
        detail={
            "message": "Docs-only service is running. Start trellis2_service.py for real generation.",
            "job_id": job_id,
            "status": "docs_only",
        },
    )


@app.get("/status/{job_id}", tags=["generation"])
async def get_status(job_id: str) -> dict:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "message": "Docs-only service does not execute generation jobs.",
    }


@app.get("/jobs", tags=["generation"])
async def list_jobs() -> dict:
    jobs = sorted(job_store.values(), key=lambda item: item["created_at"], reverse=True)
    return {"jobs": jobs}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
