import json
import re

import httpx

from ..config import RECIPE_AI_API_KEY, RECIPE_AI_API_URL, RECIPE_AI_MODEL

RECIPE_KB = {
    "红烧排骨": {
        "name": "红烧排骨",
        "category": "家常菜",
        "ingredients": ["排骨500g", "生抽2勺", "老抽1勺", "料酒1勺", "冰糖适量", "姜片3片", "八角2个", "葱段适量"],
        "steps": [
            "排骨冷水下锅，加料酒焯水去腥，捞出沥干",
            "锅中少许油，放入冰糖小火炒至焦糖色",
            "放入排骨翻炒上色",
            "加入姜片、八角、葱段炒香",
            "倒入生抽、老抽、料酒翻炒均匀",
            "加入没过排骨的热水，大火煮沸后转小火炖40分钟",
            "大火收汁至浓稠即可",
        ],
        "difficulty": "中等",
        "cook_time": "50分钟",
        "tips": "炒糖色时火不要太大，冰糖融化起泡即可下排骨",
    },
    "番茄炒蛋": {
        "name": "番茄炒蛋",
        "category": "家常菜",
        "ingredients": ["番茄2个", "鸡蛋3个", "盐适量", "糖少许", "葱花适量"],
        "steps": [
            "番茄洗净切块，鸡蛋打散加少许盐搅匀",
            "锅中热油，倒入蛋液炒至凝固盛出",
            "锅中留底油，放入番茄块翻炒出汁",
            "加入炒好的鸡蛋，加盐和少许糖调味",
            "撒上葱花，出锅装盘",
        ],
        "difficulty": "简单",
        "cook_time": "10分钟",
        "tips": "番茄要炒出汁，鸡蛋不要炒太老",
    },
    "麻婆豆腐": {
        "name": "麻婆豆腐",
        "category": "家常菜",
        "ingredients": ["嫩豆腐1盒", "猪肉末100g", "豆瓣酱1勺", "花椒粉适量", "蒜末适量", "葱花适量", "生抽1勺"],
        "steps": [
            "豆腐切小块，入沸水焯烫2分钟捞出沥干",
            "锅中热油，放入肉末炒至变色",
            "加入豆瓣酱炒出红油，放入蒜末炒香",
            "加入适量清水煮沸，放入豆腐块轻轻翻动",
            "加入生抽调味，用水淀粉勾薄芡",
            "出锅撒上花椒粉和葱花",
        ],
        "difficulty": "中等",
        "cook_time": "15分钟",
        "tips": "豆腐要轻轻翻动，避免碎裂",
    },
    "可乐鸡翅": {
        "name": "可乐鸡翅",
        "category": "家常菜",
        "ingredients": ["鸡翅中8个", "可乐1罐", "生抽2勺", "老抽1勺", "姜片3片", "料酒1勺"],
        "steps": [
            "鸡翅两面划花刀，冷水下锅焯水去腥捞出",
            "锅中少许油，放入鸡翅煎至两面金黄",
            "加入姜片、料酒、生抽、老抽翻炒上色",
            "倒入可乐没过鸡翅，大火煮沸后转小火",
            "炖煮15分钟至汤汁浓稠即可",
        ],
        "difficulty": "简单",
        "cook_time": "25分钟",
        "tips": "收汁时要不停翻动，防止糊底",
    },
    "宫保鸡丁": {
        "name": "宫保鸡丁",
        "category": "家常菜",
        "ingredients": ["鸡胸肉300g", "花生米50g", "干辣椒8个", "花椒1勺", "黄瓜丁适量", "生抽2勺", "醋1勺", "糖1勺", "淀粉适量"],
        "steps": [
            "鸡胸肉切丁，加料酒、生抽、淀粉腌制15分钟",
            "花生米炒熟备用",
            "调碗汁：生抽、醋、糖、淀粉、水混合",
            "锅中热油，放入干辣椒和花椒炒香",
            "放入鸡丁滑炒至变色",
            "倒入碗汁翻炒均匀，加入花生米和黄瓜丁即可",
        ],
        "difficulty": "中等",
        "cook_time": "20分钟",
        "tips": "花生米最后放，保持酥脆口感",
    },
    "鱼香肉丝": {
        "name": "鱼香肉丝",
        "category": "家常菜",
        "ingredients": ["猪里脊肉300g", "木耳适量", "胡萝卜1根", "青椒1个", "泡姜末适量", "蒜末适量", "豆瓣酱1勺", "生抽2勺", "醋1勺", "糖1勺"],
        "steps": [
            "猪肉切丝，加料酒、生抽、淀粉腌制10分钟",
            "木耳泡发切丝，胡萝卜、青椒切丝",
            "调鱼香汁：生抽、醋、糖、淀粉、水混合",
            "锅中热油，放入肉丝滑炒至变色盛出",
            "锅中留底油，放入豆瓣酱、泡姜末、蒜末炒香",
            "放入胡萝卜丝、木耳丝、青椒丝翻炒",
            "倒回肉丝，淋入鱼香汁翻炒均匀",
        ],
        "difficulty": "中等",
        "cook_time": "20分钟",
        "tips": "鱼香汁的比例是关键，糖醋比例约1:1",
    },
    "紫菜蛋花汤": {
        "name": "紫菜蛋花汤",
        "category": "汤羹",
        "ingredients": ["紫菜适量", "鸡蛋1个", "盐适量", "香油少许", "葱花适量"],
        "steps": [
            "鸡蛋打散备用",
            "锅中加水煮沸",
            "放入紫菜搅散",
            "淋入蛋液，待蛋花飘起后关火",
            "加盐调味，淋入香油，撒葱花",
        ],
        "difficulty": "简单",
        "cook_time": "5分钟",
        "tips": "蛋液要沿着锅边慢慢倒入，蛋花更漂亮",
    },
    "凉拌黄瓜": {
        "name": "凉拌黄瓜",
        "category": "凉菜",
        "ingredients": ["黄瓜2根", "蒜末适量", "生抽2勺", "醋1勺", "辣椒油适量", "白糖少许", "盐适量"],
        "steps": [
            "黄瓜洗净，用刀拍碎切段",
            "加入蒜末、生抽、醋、盐、白糖拌匀",
            "淋上辣椒油，拌匀即可食用",
        ],
        "difficulty": "简单",
        "cook_time": "5分钟",
        "tips": "黄瓜要现拍现拌，保持爽脆口感",
    },
    "蛋炒饭": {
        "name": "蛋炒饭",
        "category": "主食",
        "ingredients": ["隔夜米饭1碗", "鸡蛋2个", "葱花适量", "盐适量", "生抽少许"],
        "steps": [
            "鸡蛋打散，米饭打散备用",
            "锅中热油，倒入蛋液炒至凝固",
            "加入米饭大火翻炒，让每粒米都裹上蛋液",
            "加入盐和少许生抽调味",
            "撒入葱花翻炒均匀即可",
        ],
        "difficulty": "简单",
        "cook_time": "8分钟",
        "tips": "用隔夜米饭效果最好，水分少更粒粒分明",
    },
    "糖醋里脊": {
        "name": "糖醋里脊",
        "category": "家常菜",
        "ingredients": ["猪里脊300g", "鸡蛋1个", "淀粉适量", "番茄酱3勺", "白醋2勺", "糖2勺", "盐少许"],
        "steps": [
            "里脊切条，加盐、料酒腌制10分钟",
            "加入鸡蛋液和淀粉拌匀",
            "锅中多放油，六成热时放入里脊炸至金黄捞出",
            "油温升至八成热，复炸一次至酥脆",
            "锅中留少许底油，加入番茄酱、白醋、糖、少许水煮沸",
            "倒入炸好的里脊快速翻炒均匀",
        ],
        "difficulty": "中等",
        "cook_time": "25分钟",
        "tips": "复炸一次能让里脊更酥脆",
    },
    "酸辣土豆丝": {
        "name": "酸辣土豆丝",
        "category": "家常菜",
        "ingredients": ["土豆2个", "干辣椒5个", "花椒少许", "醋2勺", "盐适量", "葱花适量"],
        "steps": [
            "土豆去皮切细丝，泡入清水洗去淀粉",
            "锅中热油，放入干辣椒和花椒炒香",
            "捞出土豆丝沥干，放入锅中大火翻炒",
            "沿锅边淋入醋，翻炒均匀",
            "加盐调味，撒葱花出锅",
        ],
        "difficulty": "简单",
        "cook_time": "10分钟",
        "tips": "土豆丝要泡水去淀粉，炒出来才脆",
    },
    "水煮肉片": {
        "name": "水煮肉片",
        "category": "家常菜",
        "ingredients": ["猪里脊300g", "豆芽200g", "郫县豆瓣酱2勺", "花椒1勺", "干辣椒8个", "蒜末适量", "生抽1勺", "料酒1勺", "淀粉适量"],
        "steps": [
            "猪肉切薄片，加料酒、生抽、淀粉腌制15分钟",
            "豆芽焯水铺在碗底",
            "锅中热油，放入豆瓣酱炒出红油",
            "加入适量水煮沸，放入肉片滑散",
            "肉片变色后捞出铺在豆芽上",
            "撒上蒜末、干辣椒、花椒",
            "另起锅烧热油，浇在辣椒花椒上激出香味",
        ],
        "difficulty": "中等",
        "cook_time": "25分钟",
        "tips": "肉片要切薄，腌制后口感更嫩",
    },
    "白灼虾": {
        "name": "白灼虾",
        "category": "家常菜",
        "ingredients": ["鲜虾500g", "姜片3片", "料酒1勺", "生抽2勺", "醋1勺", "蒜末适量", "香油少许"],
        "steps": [
            "虾剪去虾须，挑出虾线",
            "锅中加水，放入姜片和料酒煮沸",
            "放入虾煮至变红卷曲，约2-3分钟",
            "捞出沥干摆盘",
            "蘸料：生抽、醋、蒜末、香油混合",
        ],
        "difficulty": "简单",
        "cook_time": "10分钟",
        "tips": "虾不要煮太久，变红即可捞出，否则肉质变老",
    },
}


def match_recipe_kb(dish_name: str) -> dict | None:
    name = dish_name.strip()
    if name in RECIPE_KB:
        return RECIPE_KB[name]
    for key in RECIPE_KB:
        if key in name or name in key:
            return RECIPE_KB[key]
    return None


def extract_dish_name(message: str) -> tuple[str, str]:
    message = message.strip()
    separators = ["，", ",", "。", "！", "!", "？", "?", "的做法", "怎么做", "怎么做啊"]
    name = message
    hints = ""
    for sep in separators:
        if sep in message:
            parts = message.split(sep, 1)
            name = parts[0].strip()
            hints = parts[1].strip() if len(parts) > 1 else ""
            break
    name = re.sub(r"(帮我|请|做一个?|来一个?|想吃|要)", "", name).strip()
    return name, hints


async def generate_recipe_with_ai(dish_name: str, user_hints: str = "") -> dict | None:
    if not RECIPE_AI_API_URL:
        return None

    prompt = f"""你是一个中餐菜谱专家。请为「{dish_name}」生成一个家常菜谱。
{f"用户的特别要求：{user_hints}" if user_hints else ""}
请严格按以下JSON格式返回，不要包含任何其他内容或markdown标记：
{{"name":"菜名","category":"分类","ingredients":["食材1 用量","食材2 用量"],"steps":["步骤1","步骤2"],"difficulty":"简单/中等/较难","cook_time":"时间","tips":"小贴士"}}

分类只能是：家常菜、汤羹、快手菜、甜品、凉菜、主食、烧烤、饮品"""

    api_url = RECIPE_AI_API_URL.rstrip("/")
    if not api_url.endswith("/chat/completions"):
        api_url += "/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                json={
                    "model": RECIPE_AI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                headers={"Authorization": f"Bearer {RECIPE_AI_API_KEY}"} if RECIPE_AI_API_KEY else {},
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            recipe = json.loads(content)
            required_keys = ["name", "category", "ingredients", "steps"]
            if all(k in recipe for k in required_keys):
                recipe.setdefault("difficulty", "中等")
                recipe.setdefault("cook_time", "")
                recipe.setdefault("tips", "")
                return recipe
            return None
    except Exception:
        return None


def build_recipe_preview(recipe: dict) -> str:
    ingredients = recipe.get("ingredients", [])
    steps = recipe.get("steps", [])
    ingredient_text = "、".join(ingredients[:8])
    if len(ingredients) > 8:
        ingredient_text += f" 等{len(ingredients)}种食材"

    steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))

    return (
        f"已为你生成「{recipe['name']}」的菜谱：\n\n"
        f"📂 分类：{recipe.get('category', '家常菜')}\n"
        f"⏱ 时间：{recipe.get('cook_time', '未知')}\n"
        f"📊 难度：{recipe.get('difficulty', '中等')}\n\n"
        f"🥬 食材：\n  {ingredient_text}\n\n"
        f"👨‍🍳 做法：\n{steps_text}"
        + (f"\n\n💡 小贴士：{recipe['tips']}" if recipe.get("tips") else "")
    )
