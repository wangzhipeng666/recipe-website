import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from ..config import UPLOAD_DIR
from ..schemas.recipe import ImageGenerateRequest, ImageGenerateResponse
from ..services.image_service import generate_image, get_task_status, submit_image_task

router = APIRouter(prefix="/api/images", tags=["images"])


class AsyncGenerateRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 768
    steps: int = 4


class AsyncGenerateResponse(BaseModel):
    task_id: int
    status: str
    status_url: str
    image_url: str


@router.post("/upload")
async def upload_image(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = Path(UPLOAD_DIR) / filename

    content = await file.read()
    filepath.write_bytes(content)

    return {"image_url": f"/api/uploads/{filename}"}


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_recipe_image(req: ImageGenerateRequest):
    image_url = await generate_image(req.name)
    if not image_url:
        raise HTTPException(
            status_code=503,
            detail="图片生成服务不可用",
        )
    return ImageGenerateResponse(image_url=image_url)


@router.post("/generate-async", response_model=AsyncGenerateResponse)
async def generate_image_async(req: AsyncGenerateRequest):
    try:
        data = await submit_image_task(req.prompt, req.width, req.height, req.steps)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"提交生成任务失败: {e}")

    task_id = data.get("id")
    if not task_id:
        raise HTTPException(status_code=502, detail="未获取到任务 ID")

    return AsyncGenerateResponse(
        task_id=task_id,
        status=data.get("status", "pending"),
        status_url=f"/api/images/status/{task_id}",
        image_url=data.get("imageUrl", ""),
    )


@router.get("/status/{task_id}")
async def image_task_status(task_id: int):
    try:
        data = await get_task_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"查询状态失败: {e}")

    result = {
        "task_id": task_id,
        "status": data.get("status", "unknown"),
    }

    if data.get("status") == "completed":
        image_url = data.get("imageUrl", "")
        if image_url:
            from ..services.image_service import _download_image
            local_url = await _download_image(image_url)
            result["image_url"] = local_url
        else:
            result["status"] = "failed"

    if data.get("error_message"):
        result["error_message"] = data["error_message"]

    return result
