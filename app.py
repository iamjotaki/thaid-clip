# -*- coding: utf-8 -*-
"""
ThaiD Clip AI Studio - Web Application Server
Production FastAPI Backend for https://clip.thaid.online
Generates 9:16 Vertical Shorts/Reels/TikTok Videos with Thai Narration & Subtitles
"""

import os
import sys
import time
import json
import uuid
import shutil
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

import clip_engine as ce

app = FastAPI(
    title="ThaiD Clip AI Studio",
    description="Automated 9:16 Vertical Video Studio for TikTok, Reels, and Shorts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


class GenerateScriptRequest(BaseModel):
    topic: str
    style: str = "affiliate"  # affiliate, storytelling, review, knowledge, news


class QuickCreateRequest(BaseModel):
    project_id: Optional[str] = None
    topic: str
    style: str = "affiliate"
    engine: str = "flux"  # flux or flow
    bgm_enabled: bool = True


class AssembleVideoRequest(BaseModel):
    project_id: str
    scenes: List[Dict[str, Any]]
    bgm_enabled: bool = True


@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "ThaiD Clip AI Studio Live"}


@app.get("/dashboard")
def serve_dashboard():
    dashboard_file = os.path.join(STATIC_DIR, "dashboard.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return {"message": "User Dashboard"}


@app.get("/admin")
def serve_admin():
    admin_file = os.path.join(STATIC_DIR, "admin.html")
    if os.path.exists(admin_file):
        return FileResponse(admin_file)
    return {"message": "Admin Portal"}


@app.get("/api/status")
def get_system_status():
    """Health check and engine status."""
    total_clips = len(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else 0
    return {
        "ok": True,
        "service": "ThaiD Clip AI Studio",
        "domain": "clip.thaid.online",
        "status": "online",
        "total_projects": total_clips,
        "engines": {
            "script": "Gemini 3.5 Flash Lite (Multi-Key Rotation)",
            "voice": "Google Thai TTS Engine (gTTS)",
            "visual_fast": "Flux Turbo 9:16 REST",
            "visual_cinematic": "Google Flow Veo (VM 1 Cloud Service)"
        },
        "video_specs": {
            "aspect_ratio": "9:16 (Vertical)",
            "resolution": "1080x1920 Full HD",
            "fps": 30,
            "audio": "AAC 128k Stereo + Auto BGM Ducking"
        }
    }


@app.post("/api/script/generate")
def api_generate_script(req: GenerateScriptRequest):
    """Generates viral 3-scene script in Thai using Gemini."""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    try:
        script = ce.generate_viral_script_gemini(req.topic, req.style)
        return {"ok": True, "script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quick-create")
def api_quick_create(req: QuickCreateRequest):
    """
    End-to-End One-Click Auto Pipeline:
    1. Generates 3-scene viral script with Gemini
    2. Generates 9:16 visual for each scene (Flux / Flow)
    3. Generates Thai voiceover & calculates exact durations
    4. Renders and concatenates into 1080x1920 MP4 with BGM!
    """
    proj_id = req.project_id or f"clip_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    proj_dir = os.path.join(OUTPUT_DIR, proj_id)
    os.makedirs(proj_dir, exist_ok=True)

    t0 = time.time()
    try:
        # 1. Script Generation
        script = ce.generate_viral_script_gemini(req.topic, req.style)
        scenes = script.get("scenes", [])
        if not scenes:
            raise HTTPException(status_code=500, detail="Failed to generate scenes")

        scenes_data = []

        # 2. Generate Assets for each scene
        for sc in scenes:
            idx = sc["id"]
            img_path = os.path.join(proj_dir, f"scene_{idx:02d}_vis.png")
            aud_path = os.path.join(proj_dir, f"scene_{idx:02d}_aud.mp3")

            prompt = sc.get("visual_prompt", f"Cinematic 9:16 commercial of {req.topic}")

            # Visual generation
            if req.engine == "flow":
                ce.generate_scene_flow(prompt, img_path)
            else:
                ce.generate_scene_image_flux(prompt, img_path)

            # Voiceover generation
            speech_text = sc.get("speech_text", "")
            _, duration = ce.generate_voiceover(speech_text, aud_path)

            scenes_data.append({
                "id": idx,
                "heading": sc.get("heading", ""),
                "speech_text": speech_text,
                "subtitle_text": sc.get("subtitle_text", sc.get("heading", "")),
                "visual_path": img_path,
                "audio_path": aud_path,
                "duration": max(2.5, duration)
            })

        # 3. Assemble and Render Final Video
        final_video_path = ce.render_full_clip_project(proj_id, scenes_data, bgm_enabled=req.bgm_enabled)
        elapsed = round(time.time() - t0, 1)

        # Save project manifest
        manifest_file = os.path.join(proj_dir, "manifest.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump({
                "project_id": proj_id,
                "topic": req.topic,
                "title": script.get("title", req.topic),
                "scenes": scenes_data,
                "video_file": os.path.basename(final_video_path),
                "elapsed": elapsed,
                "created_at": time.time()
            }, f, ensure_ascii=False, indent=2)

        return {
            "ok": True,
            "project_id": proj_id,
            "title": script.get("title", req.topic),
            "video_url": f"/output/{proj_id}/clip_{proj_id}.mp4?t={int(time.time())}",
            "elapsed": elapsed,
            "file_size_bytes": os.path.getsize(final_video_path),
            "scenes": scenes_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{project_id}")
def api_download_video(project_id: str):
    """Direct download of master MP4 video."""
    video_path = os.path.join(OUTPUT_DIR, project_id, f"clip_{project_id}.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(video_path, filename=f"ThaiD_Clip_{project_id}.mp4", media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8092, reload=True)
