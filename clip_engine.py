# -*- coding: utf-8 -*-
"""
ThaiD Clip AI Engine - 9:16 Vertical Video & Short Creator
Supports:
1. Gemini 3.5 Flash Lite Viral Script Generator
2. Dual Visual Engine:
   - Fast Flux Turbo REST (9:16 720x1280 / 1080x1920 in 4-6s)
   - Google Flow Cloud REST (Veo Video Generation on 129.221.220.121:9222/9223)
   - Procedural Aesthetic Fallback
3. Pristine Thai Voiceover (gTTS) with Auto Duration Calculation
4. Dynamic Pillow Subtitle Badge Compositor (Zero vowel drop/float artifacts)
5. FFmpeg 9:16 Video Assembler with Ken Burns Zoom & BGM Mixing
"""

import os
import sys
import re
import time
import json
import uuid
import random
import subprocess
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_PROMPT = os.path.join(FONTS_DIR, "Prompt-SemiBold.ttf")
FONT_KANIT = os.path.join(FONTS_DIR, "Kanit-Bold.ttf")
BGM_CHILL_PATH = os.path.join(ASSETS_DIR, "bgm_chill.mp3")

# Remote Google Flow Server (yayni VM 1)
REMOTE_FLOW_HOST = "129.221.220.121"
SSH_KEY = r"C:\NV\oracle_key.pem"

# Gemini API Keys from Environment
def get_gemini_keys() -> List[str]:
    keys = []
    env_k = os.environ.get("GEMINI_API_KEY", "")
    if env_k:
        keys.append(env_k.strip())
    env_pool = os.environ.get("GEMINI_KEYS_POOL", "")
    if env_pool:
        keys.extend([k.strip() for k in env_pool.split(",") if k.strip()])
    return keys


def clean_text_for_speech(text: str) -> str:
    """Cleans emojis, hashtags, URLs, and markdown for natural Thai speech."""
    if not text:
        return ""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = re.sub(r'[*_~`#]', '', text)
    text = re.sub(r'[🔴⚡🔥👑⚽🏆📊💬⭐📌🛒👉❌✅🦅🚨💥🧸🌸✏️👾🎨]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def get_audio_duration(audio_path: str) -> float:
    """Calculates exact duration of audio file using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        size = os.path.getsize(audio_path)
        return max(3.0, round(size / 16000.0, 1))


def generate_voiceover(text: str, output_path: str, lang: str = "th") -> Tuple[str, float]:
    """Generates speech via gTTS and returns path and duration in seconds."""
    from gtts import gTTS
    clean = clean_text_for_speech(text)
    if not clean:
        clean = "สวัสดีครับ วันนี้มีเรื่องราวสุดพิเศษมาแบ่งปันครับ"
    
    tts = gTTS(text=clean, lang=lang, slow=False)
    tts.save(output_path)
    dur = get_audio_duration(output_path)
    return output_path, dur


def create_fallback_aesthetic_image(text_topic: str, output_path: str, width: int = 1080, height: int = 1920) -> str:
    """Creates a beautiful luxury dark-gradient backdrop image with glowing accents."""
    img = Image.new("RGB", (width, height), (16, 16, 20))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(14 + ratio * 20)
        g = int(14 + ratio * 28)
        b = int(22 + ratio * 45)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Glow accents
    draw.ellipse([width * 0.2, height * 0.25, width * 0.8, height * 0.55], outline=(232, 90, 45, 60), width=4)
    draw.ellipse([width * 0.25, height * 0.28, width * 0.75, height * 0.52], outline=(0, 113, 227, 40), width=3)

    img.save(output_path, format="PNG")
    return output_path


def generate_scene_image_flux(prompt: str, output_path: str, width: int = 720, height: int = 1280) -> Optional[str]:
    """Generates 9:16 vertical image using Flux Turbo REST API or aesthetic fallback."""
    # Shorten prompt for high stability
    short_prompt = prompt[:160]
    safe_prompt = urllib.parse.quote(short_prompt + ", 9:16 vertical aspect ratio, masterpiece, sharp details")
    seed = random.randint(100000, 9999999)

    urls = [
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&seed={seed}"
    ]

    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if len(data) > 5000:
                    with open(output_path, "wb") as f:
                        f.write(data)
                    return output_path
        except Exception as e:
            print(f"[FluxREST] Retrying alternate model: {e}")
            time.sleep(0.8)

    # If network or API limits fail, create an aesthetic procedural graphic to prevent any crash
    print("[FluxREST] Creating aesthetic backdrop fallback...")
    return create_fallback_aesthetic_image(prompt, output_path, width=width, height=height)


def generate_scene_flow(prompt: str, output_path: str, lane: int = 9222, timeout: int = 90) -> Optional[str]:
    """Requests generation from Google Flow on remote server (129.221.220.121)."""
    try:
        if os.name == "nt" and os.path.exists(SSH_KEY):
            payload = json.dumps({"prompt": prompt, "timeout": timeout})
            ssh_cmd = [
                "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", f"ubuntu@{REMOTE_FLOW_HOST}",
                f"""curl -s -X POST -H "Content-Type: application/json" -d '{payload}' http://127.0.0.1:{lane}/generate"""
            ]
            p = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = p.communicate(timeout=timeout + 30)
            res = json.loads(stdout)
            if res.get("ok"):
                img_url = res.get("image_url") or res.get("local_url")
                if img_url and img_url.startswith("http"):
                    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        with open(output_path, "wb") as f:
                            f.write(r.read())
                    return output_path
    except Exception as e:
        print(f"[FlowREST] Note: {e}")
    # Fallback to Flux
    return generate_scene_image_flux(prompt, output_path)


def create_subtitle_overlay_png(subtitle_text: str, output_path: str, width: int = 1080, height: int = 1920) -> str:
    """Renders high-quality Thai subtitle badge as transparent 1080x1920 overlay."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_path = FONT_PROMPT if os.path.exists(FONT_PROMPT) else None
    font_size = 44
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    clean_text = subtitle_text.strip()
    bbox = draw.textbbox((0, 0), clean_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Lower-third safe zone for TikTok/Reels (Y = ~1420 px)
    cx = width // 2
    cy = 1430
    x = cx - (tw // 2)
    y = cy - (th // 2)

    pad_x = 36
    pad_y = 18

    # Rounded pill backdrop
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y],
        radius=22,
        fill=(14, 14, 18, 220),
        outline=(232, 90, 45, 240),
        width=3
    )

    # Text rendering
    draw.text((x, y - 2), clean_text, font=font, fill=(255, 255, 255, 255))
    img.save(output_path, format="PNG")
    return output_path


def render_scene_clip(
    visual_img_path: str,
    audio_path: str,
    subtitle_text: str,
    output_scene_mp4: str,
    duration: float
) -> str:
    """
    Renders an individual 9:16 scene clip with Ken Burns motion and subtitle overlay.
    """
    sub_overlay_path = output_scene_mp4.replace(".mp4", "_sub.png")
    create_subtitle_overlay_png(subtitle_text, sub_overlay_path)

    fps = 30
    total_frames = int(duration * fps)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0008,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1080x1920:fps={fps}[zoomed];"
        f"[zoomed][1:v]overlay=0:0[vfinal]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration), "-i", visual_img_path,
        "-i", sub_overlay_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "2:a",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        output_scene_mp4
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_scene_mp4


def render_full_clip_project(
    project_id: str,
    scenes_data: List[Dict[str, Any]],
    bgm_enabled: bool = True
) -> str:
    """
    Assembles all scenes into a final viral 9:16 MP4 video with BGM ducking.
    """
    proj_dir = os.path.join(OUTPUT_DIR, project_id)
    os.makedirs(proj_dir, exist_ok=True)

    rendered_scene_paths = []
    concat_list_file = os.path.join(proj_dir, "concat_list.txt")

    for idx, sc in enumerate(scenes_data, 1):
        scene_mp4 = os.path.join(proj_dir, f"scene_{idx:02d}.mp4")
        visual_path = sc["visual_path"]
        audio_path = sc["audio_path"]
        subtitle = sc.get("subtitle_text") or sc.get("heading") or ""
        duration = sc.get("duration", 4.0)

        render_scene_clip(visual_path, audio_path, subtitle, scene_mp4, duration)
        rendered_scene_paths.append(scene_mp4)

    # Write concat list file
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in rendered_scene_paths:
            escaped = p.replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    unmixed_mp4 = os.path.join(proj_dir, "unmixed_video.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        unmixed_mp4
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    final_mp4 = os.path.join(proj_dir, f"clip_{project_id}.mp4")

    # Mix BGM if enabled
    if bgm_enabled and os.path.exists(BGM_CHILL_PATH):
        total_dur = get_audio_duration(unmixed_mp4)
        mix_filter = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume=0.18,afade=t=out:st={max(0.5, total_dur - 1.5)}:d=1.5[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", unmixed_mp4,
            "-i", BGM_CHILL_PATH,
            "-filter_complex", mix_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(total_dur),
            final_mp4
        ]
        subprocess.run(mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    else:
        if os.path.exists(final_mp4):
            os.remove(final_mp4)
        os.rename(unmixed_mp4, final_mp4)

    return final_mp4


def generate_viral_script_gemini(topic: str, style: str = "affiliate") -> Dict[str, Any]:
    """Generates viral 3-scene script in Thai using Gemini."""
    prompt = f"""คุณเป็นผู้เชี่ยวชาญการผลิตคอนเทนต์วิดีโอสั้น TikTok / Reels / YouTube Shorts สไตล์ไวรัลระดับมืออาชีพ
จงเขียนสคริปต์วิดีโอสั้นความยาวประมาณ 20-35 วินาที สำหรับหัวข้อ: "{topic}" ในสไตล์: "{style}"

ให้แบ่งเป็น 3 ฉากอย่างชัดเจน:
1. ฉากที่ 1 (Hook): คำเปิดคลิปที่หยุดนิ้วโป้งคนดูภายใน 3 วินาทีแรก
2. ฉากที่ 2 (Value / Body): เนื้อหาสำคัญ จุดเด่น หรือเรื่องราวที่ดึงดูดใจ
3. ฉากที่ 3 (Call-to-Action): ชวนคอมเมนต์ กดติดตาม หรือกดตะกร้าสั่งซื้อ

ส่งกลับเป็น JSON รูปแบบนี้เท่านั้น (ห้ามมีคำอธิบายอื่นนอก JSON):
{{
  "title": "หัวข้อคลิปที่น่าดึงดูด",
  "scenes": [
    {{
      "id": 1,
      "heading": "พาดหัวฉากที่ 1 (3-6 คำ)",
      "speech_text": "บทพูดภาษาไทยที่อ่านออกเสียงได้ลื่นไหล ไม่ต้องมีอิโมจิ",
      "subtitle_text": "ข้อความซับไตเติลสั้นๆ ไม่เกิน 20 ตัวอักษร",
      "visual_prompt": "English visual description for generating realistic 9:16 vertical image, cinematic lighting"
    }},
    {{
      "id": 2,
      "heading": "พาดหัวฉากที่ 2",
      "speech_text": "บทพูดภาษาไทยเนื้อหาตอนกลาง",
      "subtitle_text": "ข้อความซับไตเติลตอนกลาง",
      "visual_prompt": "English visual description for scene 2"
    }},
    {{
      "id": 3,
      "heading": "พาดหัวฉากที่ 3",
      "speech_text": "บทพูดเชิญชวนกดสั่งซื้อหรือติดตาม",
      "subtitle_text": "กดตะกร้าหรือติดตามได้เลย!",
      "visual_prompt": "English visual description for scene 3"
    }}
  ]
}}
"""

    try:
        from google import genai
        keys = get_gemini_keys()
        for key in keys:
            try:
                client = genai.Client(api_key=key)
                resp = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
                if resp.text:
                    clean_json = re.search(r'\{.*\}', resp.text, re.DOTALL)
                    if clean_json:
                        return json.loads(clean_json.group(0))
            except Exception as e:
                print(f"[GeminiGenAI] Error: {e}")
                continue
    except Exception as e:
        print(f"[GeminiImport] Note: {e}")

    # Fallback template
    return {
        "title": f"รีวิวเจาะลึก: {topic}",
        "scenes": [
            {
                "id": 1,
                "heading": "หยุดดูก่อนถ้าไม่อยากพลาด!",
                "speech_text": f"ใครที่กำลังมองหา {topic} บอกเลยว่าคลิปนี้ห้ามเลื่อนผ่านเด็ดขาดครับ",
                "subtitle_text": f"ห้ามพลาดเด็ดขาดกับ {topic[:12]}",
                "visual_prompt": f"Dramatic cinematic close up of {topic}, luxury atmosphere, soft studio rim lighting, 8k"
            },
            {
                "id": 2,
                "heading": "จุดเด่นสุดคุ้มค่า",
                "speech_text": "ชิ้นนี้คุ้มค่ามาก ดีไซน์สวย ใช้งานง่าย ตอบโจทย์คนรุ่นใหม่แบบเต็มสิบไม่หัก",
                "subtitle_text": "ดีไซน์สวย คุ้มค่าเกินราคา",
                "visual_prompt": f"High tech modern aesthetic showcasing {topic}, sleek elegant background, 8k"
            },
            {
                "id": 3,
                "heading": "กดสั่งซื้อได้ทันที",
                "speech_text": "พิกัดอยู่ที่ลิงก์ด้านล่างแล้ว รีบกดสั่งก่อนโปรโมชั่นดีๆ จะหมดนะครับ",
                "subtitle_text": "กดสั่งซื้อที่ตะกร้าได้เลย!",
                "visual_prompt": f"Happy person holding {topic} with joyful smile, bright sunny aesthetic, 8k"
            }
        ]
    }
