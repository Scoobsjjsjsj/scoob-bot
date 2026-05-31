"""Standalone PIL emoji generation — imported by both cogs.emojis and cogs.setup."""
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont

# (emoji_name, label, top_color_rgb, bot_color_rgb, unicode_fallback)
CLAN_EMOJI_DEFS: list[tuple] = [
    ("lider",       "LÍDER",    (0xFF, 0x00, 0x00), (0x8B, 0x00, 0x00), "👑"),
    ("co_lider",    "CO-LÍDER", (0x8B, 0x00, 0x00), (0x4B, 0x00, 0x00), "⚔️"),
    ("oficial",     "OFICIAL",  (0xFF, 0x6B, 0x00), (0xCC, 0x55, 0x00), "🛡️"),
    ("raider",      "RAIDER",   (0xFF, 0x45, 0x00), (0xCC, 0x37, 0x00), "💣"),
    ("pvp",         "PVP",      (0xFF, 0xD7, 0x00), (0xB8, 0x96, 0x0C), "🎯"),
    ("roamer",      "ROAMER",   (0x00, 0xAA, 0x00), (0x00, 0x66, 0x00), "🌿"),
    ("builder",     "BUILDER",  (0x00, 0x66, 0xFF), (0x00, 0x44, 0xCC), "🏗️"),
    ("eletricista", "ELETRIC",  (0x00, 0xBF, 0xFF), (0x00, 0x80, 0xFF), "⚡"),
    ("farmer",      "FARMER",   (0x00, 0x64, 0x00), (0x00, 0x40, 0x00), "🌾"),
    ("botfarmer",   "BOTFARM",  (0x80, 0x80, 0x80), (0x50, 0x50, 0x50), "🤖"),
    ("scout",       "SCOUT",    (0x8B, 0x00, 0xFF), (0x5B, 0x00, 0xCC), "🔍"),
    ("membro",      "MEMBRO",   (0x00, 0x00, 0x8B), (0x00, 0x00, 0x66), "🎮"),
    ("recruta",     "RECRUTA",  (0x40, 0x40, 0x40), (0x20, 0x20, 0x20), "🆕"),
    ("scoob",       "SCOOB",    (0xCC, 0x44, 0x00), (0x88, 0x22, 0x00), "🦀"),
]

SIZE   = 128
RADIUS = 24


def _find_font(size: int):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def _pick_font_size(text: str) -> int:
    n = len(text)
    if n <= 2:  return 54
    if n <= 4:  return 46
    if n <= 6:  return 38
    if n <= 8:  return 30
    return 22


def generate_emoji_png(label: str,
                        color_top: tuple[int, int, int],
                        color_bot: tuple[int, int, int]) -> bytes:
    """Generate a 128×128 RGBA PNG with gradient background, rounded corners, drop-shadow text."""
    # 1. Gradient fill (vertical)
    base = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(base)
    for y in range(SIZE):
        t  = y / (SIZE - 1)
        r  = int(color_top[0] + t * (color_bot[0] - color_top[0]))
        g  = int(color_top[1] + t * (color_bot[1] - color_top[1]))
        b  = int(color_top[2] + t * (color_bot[2] - color_top[2]))
        draw.line([(0, y), (SIZE - 1, y)], fill=(r, g, b))

    # 2. Rounded-corner alpha mask
    result = base.convert("RGBA")
    mask   = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=RADIUS, fill=255
    )
    result.putalpha(mask)

    # 3. Text with drop shadow
    draw2     = ImageDraw.Draw(result)
    font_size = _pick_font_size(label)
    font      = _find_font(font_size)

    bbox = draw2.textbbox((0, 0), label, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    x    = (SIZE - tw) // 2 - bbox[0]
    y    = (SIZE - th) // 2 - bbox[1]

    # Shadow
    draw2.text((x + 2, y + 3), label, fill=(0, 0, 0, 180), font=font)
    # White text
    draw2.text((x, y), label, fill=(255, 255, 255, 255), font=font)

    buf = io.BytesIO()
    result.save(buf, "PNG")
    return buf.getvalue()


async def create_emojis(guild, existing_names: set[str]) -> tuple[list, list[str], list[str]]:
    """Creates all clan emojis on the guild. Returns (created_emojis, skipped, failed)."""
    import discord
    created, skipped, failed = [], [], []
    for name, label, top, bot, _ in CLAN_EMOJI_DEFS:
        if name in existing_names:
            skipped.append(name)
            continue
        try:
            image_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_emoji_png, label, top, bot
            )
            emoji = await guild.create_custom_emoji(name=name, image=image_bytes, reason="/setupemojis")
            created.append(emoji)
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            raise
        except Exception as e:
            failed.append(f"`{name}`: {e}")
    return created, skipped, failed
