"""服务端图形验证码生成与校验"""

import base64
import io
import random
import string
import uuid

from PIL import Image, ImageDraw, ImageFont

from app.core.redis import RedisClient

# 验证码配置
CAPTCHA_WIDTH = 160
CAPTCHA_HEIGHT = 60
CAPTCHA_LENGTH = 4
CAPTCHA_TTL = 300  # 5分钟过期
CAPTCHA_FONT_SIZE = 36
CAPTCHA_KEY_PREFIX = "captcha:"


def _generate_code(length: int = CAPTCHA_LENGTH) -> str:
    """生成随机验证码（去除易混淆字符）"""
    chars = string.ascii_uppercase + string.digits
    # 去除易混淆字符
    chars = chars.translate(str.maketrans("", "", "0O1I2Z5S8B"))
    return "".join(random.choice(chars) for _ in range(length))


def _create_captcha_image(code: str) -> bytes:
    """生成验证码图片，返回 PNG 字节流"""
    width, height = CAPTCHA_WIDTH, CAPTCHA_HEIGHT
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 尝试使用系统字体，否则使用默认
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", CAPTCHA_FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", CAPTCHA_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default(size=CAPTCHA_FONT_SIZE)

    # 绘制验证码字符
    char_width = width // (len(code) + 1)
    for i, char in enumerate(code):
        x = char_width * i + random.randint(10, 20)
        y = random.randint(5, 15)
        color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        draw.text((x, y), char, fill=color, font=font)

    # 绘制干扰线
    for _ in range(4):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        draw.line((x1, y1, x2, y2), fill=color, width=1)

    # 绘制干扰点
    for _ in range(50):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.point((x, y), fill=color)

    # 输出 PNG 字节流
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def generate_captcha(redis: RedisClient) -> tuple[str, str]:
    """
    生成验证码

    :param redis: Redis 客户端
    :return: (captcha_key, base64_image)
    """
    code = _generate_code()
    captcha_key = str(uuid.uuid4())
    redis_key = f"{CAPTCHA_KEY_PREFIX}{captcha_key}"

    # 存入 Redis，TTL 5分钟
    await redis.set(redis_key, code.upper(), ex=CAPTCHA_TTL)

    # 生成图片并转为 base64
    image_bytes = _create_captcha_image(code)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    return captcha_key, f"data:image/png;base64,{b64_image}"


async def verify_captcha(redis: RedisClient, captcha_key: str, captcha_code: str | None) -> bool:
    """
    验证验证码（一次性使用，验证后立即删除）

    :param redis: Redis 客户端
    :param captcha_key: 验证码 key
    :param captcha_code: 用户输入的验证码
    :return: 是否验证通过
    """
    if captcha_code is None:
        return False

    redis_key = f"{CAPTCHA_KEY_PREFIX}{captcha_key}"

    # 获取并删除（原子操作用 pipeline）
    results = await redis.pipeline_exec(
        [
            ("get", redis_key),
            ("delete", redis_key),
        ]
    )

    stored_code = results[0]
    if stored_code is None:
        return False

    return stored_code.upper() == captcha_code.upper()
