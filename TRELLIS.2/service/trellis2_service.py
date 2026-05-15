"""
TRELLIS.2 FastAPI service — single-GPU image-to-3D generation.
Start:  PY_SSIZE_T_CLEAN=1 CUDA_VISIBLE_DEVICES=1 python trellis2_service.py
"""
import os
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import sys
import json
import time
import uuid
import asyncio
import logging
from pathlib import Path
from io import BytesIO
from typing import Optional

import cv2
import imageio
import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Ensure TRELLIS.2 source is on path
TRELLIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TRELLIS_ROOT))

from trellis2.pipelines import Trellis2ImageTo3DPipeline
from trellis2.utils import render_utils
from trellis2.renderers import EnvMap
import o_voxel

# ---------- compat patches (same as smoke_test) ----------
import transformers.modeling_utils as modeling_utils
_orig_move = modeling_utils.PreTrainedModel._move_missing_keys_from_meta_to_device
def _patched_move(self, *args, **kwargs):
    if not hasattr(self, 'all_tied_weights_keys'):
        twk = getattr(self, '_tied_weights_keys', None)
        self.all_tied_weights_keys = twk if twk is not None else {}
    return _orig_move(self, *args, **kwargs)
modeling_utils.PreTrainedModel._move_missing_keys_from_meta_to_device = _patched_move

# ---------- config ----------
HOST = "0.0.0.0"
PORT = 9020
OUTPUT_DIR = Path("/data/fj/数字孪生/digital-twingo/scene-server-go/scene-assets")
MODEL_DIR = OUTPUT_DIR / "models"
THUMB_DIR = OUTPUT_DIR / "thumbs"
WEIGHTS_PATH = TRELLIS_ROOT / "TRELLIS.2-4B"
HDRI_PATH = TRELLIS_ROOT / "assets/hdri/forest.exr"

for d in [MODEL_DIR, THUMB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("trellis2-service")

# ---------- globals ----------
pipeline: Optional[Trellis2ImageTo3DPipeline] = None
envmap: Optional[EnvMap] = None
task_queue: asyncio.Queue = None
worker_task = None
job_store: dict = {}  # job_id -> {status, progress, result, error}

# ---------- fastapi ----------
app = FastAPI(title="TRELLIS.2 Image-to-3D Service", version="1.0.0")


async def run_generation(job: dict):
    """Run a single generation job (called by background worker)."""
    job_id = job["job_id"]
    try:
        job["status"] = "running"
        logger.info(f"[{job_id}] Starting generation (resolution={job['resolution']})")

        # Load image
        image = Image.open(job["image_path"]).convert("RGB")

        # Run pipeline
        mesh = pipeline.run(image)[0]
        mesh.simplify(16777216)

        job["progress"] = 80

        # Export GLB
        glb = o_voxel.postprocess.to_glb(
            vertices=mesh.vertices,
            faces=mesh.faces,
            attr_volume=mesh.attrs,
            coords=mesh.coords,
            attr_layout=mesh.layout,
            voxel_size=mesh.voxel_size,
            aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
            decimation_target=job["decimation_target"],
            texture_size=job["texture_size"],
            remesh=True,
            remesh_band=1,
            remesh_project=0,
            verbose=False,
        )
        glb_path = MODEL_DIR / f"{job_id}.glb"
        glb.export(str(glb_path))
        logger.info(f"[{job_id}] GLB saved: {glb_path} ({glb_path.stat().st_size / 1e6:.1f} MB)")

        # Generate thumbnail (first frame of turntable video)
        thumb_path = THUMB_DIR / f"{job_id}.jpg"
        video = render_utils.make_pbr_vis_frames(render_utils.render_video(mesh, envmap=envmap))
        if video:
            first_frame = video[0]
            imageio.imwrite(str(thumb_path), first_frame)
        logger.info(f"[{job_id}] Thumbnail saved: {thumb_path}")

        job["status"] = "completed"
        job["result"] = {
            "glb_url": f"/scene-assets/models/{job_id}.glb",
            "thumb_url": f"/scene-assets/thumbs/{job_id}.jpg",
            "file_size": glb_path.stat().st_size,
        }
        job["progress"] = 100
        logger.info(f"[{job_id}] Completed")

    except Exception as e:
        logger.exception(f"[{job_id}] Failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)

    finally:
        # Clean up uploaded image
        img_path = Path(job.get("image_path", ""))
        if img_path.exists():
            img_path.unlink(missing_ok=True)


async def worker():
    """Background worker: processes one job at a time from the queue."""
    logger.info("Worker started, waiting for jobs...")
    while True:
        job = await task_queue.get()
        try:
            await run_generation(job)
        except Exception as e:
            logger.exception(f"Worker error: {e}")
        finally:
            task_queue.task_done()
            torch.cuda.empty_cache()


@app.on_event("startup")
async def startup():
    global pipeline, envmap, task_queue, worker_task

    logger.info(f"Loading TRELLIS.2 pipeline from {WEIGHTS_PATH}...")
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}, VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    envmap = EnvMap(torch.tensor(
        cv2.cvtColor(cv2.imread(str(HDRI_PATH), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB),
        dtype=torch.float32, device='cuda'
    ))

    pipeline = Trellis2ImageTo3DPipeline.from_pretrained(str(WEIGHTS_PATH))
    pipeline.cuda()
    logger.info("Pipeline loaded.")

    task_queue = asyncio.Queue()
    worker_task = asyncio.create_task(worker())


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_loaded": pipeline is not None}


@app.post("/generate")
async def generate(
    image: UploadFile = File(...),
    resolution: int = Form(512),
    decimation_target: int = Form(300000),
    texture_size: int = Form(2048),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not loaded yet")

    if resolution not in (512, 1024, 1536):
        raise HTTPException(400, "Resolution must be 512, 1024, or 1536")

    job_id = uuid.uuid4().hex[:12]
    img_path = f"/tmp/trellis2_input_{job_id}.png"

    contents = await image.read()
    pil_img = Image.open(BytesIO(contents)).convert("RGB")
    pil_img.save(img_path, "PNG")

    job = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "image_path": img_path,
        "resolution": resolution,
        "decimation_target": decimation_target,
        "texture_size": texture_size,
        "result": None,
        "error": None,
        "created_at": time.time(),
    }
    job_store[job_id] = job

    await task_queue.put(job)
    queue_position = task_queue.qsize()

    logger.info(f"[{job_id}] Queued (position {queue_position}, resolution={resolution})")
    return {"job_id": job_id, "status": "queued", "queue_position": queue_position}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    resp = {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
    }
    if job["status"] == "completed":
        resp["result"] = job["result"]
    elif job["status"] == "failed":
        resp["error"] = job["error"]
    else:
        resp["queue_position"] = task_queue.qsize() if job["status"] == "queued" else 0

    return resp


@app.get("/jobs")
async def list_jobs():
    """List all jobs (newest first). For MVP; add filtering later."""
    result = []
    for job_id, job in sorted(job_store.items(), key=lambda x: x[1]["created_at"], reverse=True):
        result.append({
            "job_id": job["job_id"],
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "resolution": job.get("resolution"),
        })
    return {"jobs": result}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
