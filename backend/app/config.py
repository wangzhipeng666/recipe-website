from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = "sqlite:///./recipes.db"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://47.93.230.201:6677")
COMFYUI_API_KEY = os.getenv("COMFYUI_API_KEY", "xsk_8bb4af48404240e314f3e1dc19097e5e2810acf8547988c2")

RECIPE_AI_API_URL = os.getenv("RECIPE_AI_API_URL", "")
RECIPE_AI_API_KEY = os.getenv("RECIPE_AI_API_KEY", "")
RECIPE_AI_MODEL = os.getenv("RECIPE_AI_MODEL", "gpt-3.5-turbo")
