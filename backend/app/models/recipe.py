from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(10), nullable=False, default="🍽️")

    recipes = relationship("Recipe", back_populates="category")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    image_url = Column(String(500), nullable=True, default="")
    images = Column(Text, nullable=False, default="[]")
    ingredients = Column(Text, nullable=False, default="[]")
    steps = Column(Text, nullable=False, default="[]")
    difficulty = Column(String(10), nullable=False, default="简单")
    cook_time = Column(String(20), nullable=False, default="")
    tips = Column(Text, nullable=True, default="")
    is_favorite = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="recipes")
