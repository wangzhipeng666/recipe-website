import asyncio
import uuid
from pathlib import Path

import httpx

from ..config import COMFYUI_API_KEY, COMFYUI_API_URL, UPLOAD_DIR


async def generate_image(recipe_name: str) -> str:
    if not COMFYUI_API_URL:
        return ""

    prompt = f"一道精美的中式菜肴：{recipe_name}，美食摄影风格，高清，暖色调，白色盘子，自然光"

    task_id = await _submit_task(prompt)
    if not task_id:
        return ""

    image_url = await _wait_for_completion(task_id)
    if not image_url:
        return ""

    local_url = await _download_image(image_url)
    return local_url


async def submit_image_task(prompt: str, width: int = 1024, height: int = 768, steps: int = 4) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{COMFYUI_API_URL}/service/image/generate",
            json={"prompt": prompt, "width": width, "height": height, "steps": steps},
            headers={"X-Service-Key": COMFYUI_API_KEY},
        )
        response.raise_for_status()
        return response.json()


async def get_task_status(task_id: int) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{COMFYUI_API_URL}/service/image/status/{task_id}",
            headers={"X-Service-Key": COMFYUI_API_KEY},
        )
        response.raise_for_status()
        return response.json()


async def _submit_task(prompt: str) -> int | None:
    try:
        data = await submit_image_task(prompt)
        return data.get("id")
    except Exception:
        return None


async def _wait_for_completion(task_id: int, max_wait: int = 180) -> str | None:
    for _ in range(max_wait // 5):
        await asyncio.sleep(5)
        try:
            data = await get_task_status(task_id)
            status = data.get("status", "")
            if status == "completed":
                return data.get("imageUrl", "")
            if status == "failed":
                return None
        except Exception:
            return None
    return None


async def _download_image(image_url: str) -> str:
    full_url = f"{COMFYUI_API_URL}{image_url}" if image_url.startswith("/") else image_url
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(full_url)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        ext = "jpg" if "jpeg" in content_type else "png"

        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = Path(UPLOAD_DIR) / filename
        filepath.write_bytes(response.content)

        return f"/api/uploads/{filename}"
