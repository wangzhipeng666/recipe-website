from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    icon: str = "🍽️"


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    model_config = {"from_attributes": True}


class RecipeBase(BaseModel):
    name: str
    category_id: int
    image_url: str = ""
    images: str = "[]"
    ingredients: str = "[]"
    steps: str = "[]"
    difficulty: str = "简单"
    cook_time: str = ""
    tips: str = ""


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    ingredients: Optional[str] = None
    steps: Optional[str] = None
    difficulty: Optional[str] = None
    cook_time: Optional[str] = None
    tips: Optional[str] = None


class RecipeResponse(RecipeBase):
    id: int
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}


class RecipeListResponse(BaseModel):
    items: list[RecipeResponse]
    total: int
    page: int
    size: int


class ImageGenerateRequest(BaseModel):
    name: str


class ImageGenerateResponse(BaseModel):
    image_url: str


class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"


class ChatRecipePreview(BaseModel):
    name: str
    category: str
    ingredients: list[str]
    steps: list[str]
    difficulty: str = "中等"
    cook_time: str = ""
    tips: str = ""


class ChatResponse(BaseModel):
    type: str  # "text" | "recipe_preview" | "confirm" | "error"
    message: str
    recipe: Optional[ChatRecipePreview] = None
    recipe_id: Optional[int] = None
    recipe_name: Optional[str] = None
