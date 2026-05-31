"""Shared utilities for all cogs."""
from datetime import datetime, timezone
import discord

# ── Theme colors ──────────────────────────────────────────────────────────────
RUST_COLOR  = discord.Color.from_rgb(180, 60, 10)
RUST_RED    = discord.Color.from_rgb(200, 30, 10)
RUST_ORANGE = discord.Color.from_rgb(220, 100, 10)
RUST_GOLD   = discord.Color.from_rgb(220, 160, 10)

AUTONAME_PREFIX = "𝗦𝗰𝗼𝗼𝗯 | "

# ── Clan role definitions (ordered highest → lowest) ─────────────────────────
# (display_name, color, permissions_kwargs, hoist, nick_emoji)
CLAN_ROLE_DEFS: list[tuple] = [
    # (display_name, discord.Color, permissions_kwargs, hoist, nick_emoji)
    ("👑 Lider",      discord.Color.from_rgb(255,   0,   0),   # #FF0000
     {"administrator": True}, True, "👑"),
    ("⚔️ Co-Lider",   discord.Color.from_rgb(139,   0,   0),   # #8B0000
     {"kick_members": True, "ban_members": True, "manage_channels": True,
      "manage_messages": True, "manage_roles": True, "mention_everyone": True,
      "mute_members": True, "deafen_members": True, "move_members": True,
      "manage_nicknames": True, "manage_guild": True}, True, "⚔️"),
    ("🛡️ Oficial",    discord.Color.from_rgb(255, 107,   0),   # #FF6B00
     {"kick_members": True, "ban_members": True, "manage_messages": True,
      "manage_roles": True, "mute_members": True, "move_members": True,
      "manage_nicknames": True}, True, "🛡️"),
    ("💣 Raider",     discord.Color.from_rgb(255,  69,   0), {}, True,  "💣"),  # #FF4500
    ("🎯 PVP",        discord.Color.from_rgb(255, 215,   0), {}, True,  "🎯"),  # #FFD700
    ("🌿 Roamer",     discord.Color.from_rgb(  0, 170,   0), {}, True,  "🌿"),  # #00AA00
    ("🏗️ Builder",    discord.Color.from_rgb(  0, 102, 255), {}, True,  "🏗️"),  # #0066FF
    ("⚡ Eletricista", discord.Color.from_rgb(  0, 191, 255), {}, True,  "⚡"),  # #00BFFF
    ("🌾 Farmer",     discord.Color.from_rgb(  0, 100,   0), {}, True,  "🌾"),  # #006400
    ("🤖 BotFarmer",  discord.Color.from_rgb(128, 128, 128), {}, True,  "🤖"),  # #808080
    ("🔍 Scout",      discord.Color.from_rgb(139,   0, 255), {}, True,  "🔍"),  # #8B00FF
    ("🎮 Membro",     discord.Color.from_rgb(  0,   0, 139), {}, False, "🎮"),  # #00008B
    ("🆕 Recruta",    discord.Color.from_rgb( 64,  64,  64), {}, False, "🆕"),  # #404040
]

CLAN_ROLE_NAMES  = [r[0] for r in CLAN_ROLE_DEFS]
CLAN_ROLE_EMOJIS = {r[0]: r[4] for r in CLAN_ROLE_DEFS}
OFICIAL_PLUS     = {"👑 Lider", "⚔️ Co-Lider", "🛡️ Oficial"}

# ── Embed factory ─────────────────────────────────────────────────────────────

def rust_embed(title: str, description: str = "",
               color: discord.Color = RUST_COLOR) -> discord.Embed:
    e = discord.Embed(title=title, description=description, color=color)
    e.set_footer(text="🦀 Rust Clan Bot v2.0")
    return e

# ── Nick helpers ──────────────────────────────────────────────────────────────

def get_clan_role_emoji(member: discord.Member) -> str:
    names = {r.name for r in member.roles}
    for name, _, _, _, emoji in CLAN_ROLE_DEFS:
        if name in names:
            return emoji
    return "🆕"


def build_nick(member: discord.Member) -> str:
    emoji = get_clan_role_emoji(member)
    base  = member.name[:18]
    return f"{AUTONAME_PREFIX}{emoji} {base}"[:32]

# ── Permission helpers ────────────────────────────────────────────────────────

def has_oficial_plus(member: discord.Member) -> bool:
    return any(r.name in OFICIAL_PLUS for r in member.roles)

# ── Time helpers ──────────────────────────────────────────────────────────────

def countdown(target: datetime) -> str:
    now = datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    diff = target - now
    if diff.total_seconds() <= 0:
        return "**já aconteceu**"
    d, rem = divmod(int(diff.total_seconds()), 86400)
    h, rem = divmod(rem, 3600)
    m      = rem // 60
    parts  = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return " ".join(parts) or "< 1 min"

# ── Bold unicode ──────────────────────────────────────────────────────────────

def to_bold_unicode(text: str) -> str:
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr(0x1D5D4 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            out.append(chr(0x1D5EE + ord(ch) - ord("a")))
        elif "0" <= ch <= "9":
            out.append(chr(0x1D7EC + ord(ch) - ord("0")))
        else:
            out.append(ch)
    return "".join(out)

# ── Theme map (for /roles) ────────────────────────────────────────────────────

THEME_MAP: dict[str, tuple[str, discord.Color]] = {
    "scooby":      ("🐕", discord.Color.from_rgb(139, 90,  43)),
    "scooby-doo":  ("🐕", discord.Color.from_rgb(139, 90,  43)),
    "fire":        ("🔥", discord.Color.from_rgb(255, 69,  0)),
    "ice":         ("❄️", discord.Color.from_rgb(135, 206, 235)),
    "water":       ("💧", discord.Color.from_rgb(0,   119, 190)),
    "earth":       ("🌍", discord.Color.from_rgb(34,  139, 34)),
    "nature":      ("🌿", discord.Color.from_rgb(34,  139, 34)),
    "lightning":   ("⚡", discord.Color.from_rgb(255, 215, 0)),
    "thunder":     ("⚡", discord.Color.from_rgb(255, 215, 0)),
    "dark":        ("🌑", discord.Color.from_rgb(30,  30,  30)),
    "light":       ("✨", discord.Color.from_rgb(255, 240, 180)),
    "dragon":      ("🐉", discord.Color.from_rgb(180, 0,   0)),
    "ninja":       ("🥷", discord.Color.from_rgb(50,  50,  50)),
    "space":       ("🚀", discord.Color.from_rgb(25,  25,  112)),
    "galaxy":      ("🌌", discord.Color.from_rgb(25,  25,  112)),
    "star":        ("⭐", discord.Color.from_rgb(255, 215, 0)),
    "moon":        ("🌙", discord.Color.from_rgb(72,  61,  139)),
    "sun":         ("☀️", discord.Color.from_rgb(255, 165, 0)),
    "rose":        ("🌹", discord.Color.from_rgb(220, 20,  60)),
    "skull":       ("💀", discord.Color.from_rgb(100, 100, 100)),
    "rainbow":     ("🌈", discord.Color.from_rgb(148, 103, 189)),
    "music":       ("🎵", discord.Color.from_rgb(148, 0,   211)),
    "gaming":      ("🎮", discord.Color.from_rgb(0,   128, 128)),
    "cat":         ("🐱", discord.Color.from_rgb(255, 140, 0)),
    "dog":         ("🐶", discord.Color.from_rgb(139, 90,  43)),
    "fox":         ("🦊", discord.Color.from_rgb(255, 102, 0)),
    "wolf":        ("🐺", discord.Color.from_rgb(128, 128, 128)),
    "bear":        ("🐻", discord.Color.from_rgb(101, 67,  33)),
    "lion":        ("🦁", discord.Color.from_rgb(255, 165, 0)),
    "crown":       ("👑", discord.Color.from_rgb(255, 215, 0)),
    "diamond":     ("💎", discord.Color.from_rgb(0,   191, 255)),
    "ghost":       ("👻", discord.Color.from_rgb(200, 200, 200)),
    "vampire":     ("🧛", discord.Color.from_rgb(139, 0,   0)),
    "zombie":      ("🧟", discord.Color.from_rgb(107, 142, 35)),
    "wizard":      ("🧙", discord.Color.from_rgb(75,  0,   130)),
    "knight":      ("⚔️", discord.Color.from_rgb(192, 192, 192)),
    "angel":       ("😇", discord.Color.from_rgb(255, 255, 200)),
    "demon":       ("😈", discord.Color.from_rgb(128, 0,   128)),
    "robot":       ("🤖", discord.Color.from_rgb(0,   168, 168)),
    "alien":       ("👾", discord.Color.from_rgb(0,   200, 100)),
    "pirate":      ("🏴‍☠️", discord.Color.from_rgb(40,  40,  40)),
    "gold":        ("🥇", discord.Color.from_rgb(255, 215, 0)),
    "purple":      ("💜", discord.Color.from_rgb(128, 0,   128)),
    "rust":        ("🦀", discord.Color.from_rgb(180, 60,  10)),
    "mystery":     ("🔍", discord.Color.from_rgb(75,  0,   130)),
    "flower":      ("🌸", discord.Color.from_rgb(255, 182, 193)),
    "sport":       ("🏆", discord.Color.from_rgb(255, 165, 0)),
    "skull":       ("💀", discord.Color.from_rgb(100, 100, 100)),
    "military":    ("🎖️", discord.Color.from_rgb(80,  100, 60)),
}


# ── Server emoji helpers ──────────────────────────────────────────────────────

ROLE_TO_EMOJI_NAME: dict[str, str] = {
    "👑 Lider":       "lider",
    "⚔️ Co-Lider":    "co_lider",
    "🛡️ Oficial":     "oficial",
    "💣 Raider":      "raider",
    "🎯 PVP":         "pvp",
    "🌿 Roamer":      "roamer",
    "🏗️ Builder":     "builder",
    "⚡ Eletricista":  "eletricista",
    "🌾 Farmer":      "farmer",
    "🤖 BotFarmer":   "botfarmer",
    "🔍 Scout":       "scout",
    "🎮 Membro":      "membro",
    "🆕 Recruta":     "recruta",
}


def get_server_emoji(guild: discord.Guild, role_name: str, fallback: str) -> str:
    """Return the server's custom emoji string for a clan role, or fallback unicode."""
    emoji_name = ROLE_TO_EMOJI_NAME.get(role_name)
    if emoji_name:
        server_emoji = discord.utils.get(guild.emojis, name=emoji_name)
        if server_emoji:
            return str(server_emoji)
    return fallback


def resolve_theme(tema: str) -> tuple[str, discord.Color]:
    key = tema.lower().strip()
    if key in THEME_MAP:
        return THEME_MAP[key]
    for k, v in THEME_MAP.items():
        if k in key or key in k:
            return v
    return ("✨", discord.Color.blurple())
