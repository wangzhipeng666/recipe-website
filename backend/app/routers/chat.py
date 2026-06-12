import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.recipe import Category, Recipe
from ..schemas.recipe import ChatMessage, ChatRecipePreview, ChatResponse
from ..services.recipe_chat import (
    build_recipe_preview,
    extract_dish_name,
    generate_recipe_with_ai,
    match_recipe_kb,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

pending_recipes: dict[str, dict] = {}


def find_category_id(db: Session, category_name: str) -> int:
    cat = db.query(Category).filter(Category.name == category_name).first()
    if cat:
        return cat.id
    cat = db.query(Category).filter(Category.name == "家常菜").first()
    return cat.id if cat else 1


@router.post("", response_model=ChatResponse)
async def chat(msg: ChatMessage, db: Session = Depends(get_db)):
    text = msg.message.strip()
    sid = msg.session_id

    if sid in pending_recipes and text in ("确认", "确定", "好的", "ok", "OK"):
        recipe_data = pending_recipes.pop(sid)
        category_id = find_category_id(db, recipe_data.get("category", "家常菜"))
        recipe = Recipe(
            name=recipe_data["name"],
            category_id=category_id,
            ingredients=json.dumps(recipe_data.get("ingredients", []), ensure_ascii=False),
            steps=json.dumps(recipe_data.get("steps", []), ensure_ascii=False),
            difficulty=recipe_data.get("difficulty", "中等"),
            cook_time=recipe_data.get("cook_time", ""),
            tips=recipe_data.get("tips", ""),
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return ChatResponse(
            type="confirm",
            message=f"已将「{recipe.name}」添加到{recipe_data.get('category', '家常菜')}分类",
            recipe_id=recipe.id,
            recipe_name=recipe.name,
        )

    if text.startswith("生成图片："):
        recipe_name = text.replace("生成图片：", "").strip()
        recipe = db.query(Recipe).filter(Recipe.name == recipe_name).order_by(Recipe.id.desc()).first()
        if not recipe:
            return ChatResponse(type="text", message=f"未找到「{recipe_name}」的菜谱")

        from ..services.image_service import generate_image

        image_url = await generate_image(recipe_name)
        if image_url:
            recipe.image_url = image_url
            db.commit()
            return ChatResponse(
                type="text",
                message=f"已为「{recipe_name}」生成图片",
                recipe_name=recipe_name,
            )
        return ChatResponse(type="text", message="图片生成失败，请稍后重试")

    if sid in pending_recipes and text in ("放弃", "取消", "算了"):
        pending_recipes.pop(sid)
        return ChatResponse(type="text", message="已放弃添加。你可以继续告诉我其他菜名。")

    if sid in pending_recipes and text in ("修改", "编辑"):
        recipe_data = pending_recipes[sid]
        pending_recipes.pop(sid)
        return ChatResponse(
            type="text",
            message=(
                f"请告诉我你想怎么修改「{recipe_data['name']}」，例如：\n"
                "• 少放盐\n"
                "• 不放辣椒\n"
                "• 食材和步骤的具体调整"
            ),
        )

    if sid in pending_recipes and len(text) < 50:
        pending_recipes.pop(sid)
        name, hints = extract_dish_name(text)
        if name:
            recipe = await _generate_or_match(name, hints)
            if recipe:
                pending_recipes[sid] = recipe
                preview = build_recipe_preview(recipe)
                return ChatResponse(
                    type="recipe_preview",
                    message=preview,
                    recipe=ChatRecipePreview(**recipe),
                )
        return ChatResponse(type="text", message="抱歉，无法生成该菜谱。请换个菜名试试。")

    name, hints = extract_dish_name(text)
    if not name:
        return ChatResponse(
            type="text",
            message="请告诉我你想做什么菜，例如：\n• 红烧排骨\n• 宫保鸡丁，花生多放点\n• 番茄炒蛋",
        )

    recipe = await _generate_or_match(name, hints)
    if recipe:
        pending_recipes[sid] = recipe
        preview = build_recipe_preview(recipe)
        return ChatResponse(
            type="recipe_preview",
            message=preview,
            recipe=ChatRecipePreview(**recipe),
        )

    return ChatResponse(type="text", message="抱歉，暂时无法生成该菜谱。请换个菜名试试。")


async def _generate_or_match(name: str, hints: str = "") -> dict | None:
    recipe = match_recipe_kb(name)
    if recipe:
        return recipe

    recipe = await generate_recipe_with_ai(name, hints)
    return recipe
