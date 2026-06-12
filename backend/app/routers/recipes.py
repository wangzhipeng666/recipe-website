import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.recipe import Recipe
from ..schemas.recipe import (
    RecipeCreate,
    RecipeListResponse,
    RecipeResponse,
    RecipeUpdate,
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=RecipeListResponse)
def list_recipes(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Recipe)

    if category:
        query = query.join(Recipe.category).filter(
            Recipe.category.has(name=category)
        )

    if search:
        query = query.filter(Recipe.name.contains(search))

    total = query.count()
    items = (
        query.order_by(Recipe.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return RecipeListResponse(items=items, total=total, page=page, size=size)


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    return recipe


@router.post("", response_model=RecipeResponse, status_code=201)
def create_recipe(recipe_in: RecipeCreate, db: Session = Depends(get_db)):
    recipe = Recipe(**recipe_in.model_dump())
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int, recipe_in: RecipeUpdate, db: Session = Depends(get_db)
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")

    update_data = recipe_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recipe, field, value)

    db.commit()
    db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    db.delete(recipe)
    db.commit()


@router.post("/{recipe_id}/favorite", response_model=RecipeResponse)
def toggle_favorite(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")

    recipe.is_favorite = not recipe.is_favorite
    db.commit()
    db.refresh(recipe)
    return recipe
