from datetime import datetime, timezone
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE

# ── Game data ─────────────────────────────────────────────────────────────────

CALC_DATA = {
    "stone": {"rockets": 4,  "c4": 2,  "explo": 185, "sulfur_r": 5_600,  "sulfur_c4": 4_400,  "lgf": 400},
    "metal": {"rockets": 8,  "c4": 4,  "explo": 370, "sulfur_r": 11_200, "sulfur_c4": 8_800,  "lgf": 800},
    "hqm":   {"rockets": 15, "c4": 8,  "explo": 500, "sulfur_r": 21_000, "sulfur_c4": 17_600, "lgf": 1500},
}

BP_DATA = {
    "ak47":       {"scrap": 500,  "workbench": "T3", "time": "2m",  "mats": "Metal Pipe ×2, Metal Spring ×2, HQM ×50, Scrap ×5"},
    "lr300":      {"scrap": 500,  "workbench": "T3", "time": "1m",  "mats": "Metal Pipe ×2, HQM ×15, Metal Fragment ×200"},
    "m249":       {"scrap": 750,  "workbench": "T3", "time": "3m",  "mats": "Metal Pipe ×4, HQM ×100, Metal Fragment ×400"},
    "bolt":       {"scrap": 500,  "workbench": "T3", "time": "2m",  "mats": "Metal Pipe ×3, HQM ×20, Metal Fragment ×50"},
    "mp5":        {"scrap": 250,  "workbench": "T2", "time": "1m",  "mats": "Metal Pipe ×1, Metal Spring ×2, Metal Fragment ×100"},
    "shotgun":    {"scrap": 125,  "workbench": "T2", "time": "1m",  "mats": "Metal Pipe ×1, Metal Fragment ×100, Wood ×50"},
    "semi":       {"scrap": 75,   "workbench": "T1", "time": "30s", "mats": "Metal Pipe ×1, Metal Fragment ×75"},
    "c4":         {"scrap": 500,  "workbench": "T2", "time": "2m",  "mats": "Sulfur ×2200, Charcoal ×3000, Cloth ×10, Tech Trash ×1"},
    "rocket":     {"scrap": 250,  "workbench": "T2", "time": "1m",  "mats": "Sulfur ×1400, Gunpowder ×100, Metal Pipe ×2, LGF ×100"},
    "grenade":    {"scrap": 75,   "workbench": "T1", "time": "30s", "mats": "Sulfur ×400, Metal Fragment ×75, Charcoal ×500"},
    "hqm":        {"scrap": 125,  "workbench": "T2", "time": "1m",  "mats": "HQM Ore → Furnace → HQM"},
    "armor_hqm":  {"scrap": 500,  "workbench": "T3", "time": "2m",  "mats": "HQM ×50, Cloth ×30 (por peça)"},
    "armor_metal":{"scrap": 250,  "workbench": "T2", "time": "1m",  "mats": "Metal Fragment ×100, Leather ×15 (por peça)"},
}

DECAY_DATA = {
    "twig floor":       "1h",  "wood floor":       "3h",   "stone floor":       "5h",
    "metal floor":      "8h",  "hqm floor":        "12h",  "twig wall":         "1h",
    "wood wall":        "3h",  "stone wall":        "5h",  "metal wall":        "8h",
    "hqm wall":         "12h", "wood foundation":   "3h",  "stone foundation":  "5h",
    "metal foundation": "8h",  "hqm foundation":    "12h", "wood door":         "3h",
    "metal door":       "8h",  "hqm door":          "12h", "wooden barricade":  "1h",
    "sandbag barricade":"1h",  "concrete barricade":"3h",
}

CRAFTING_DATA = {
    "gunpowder":   {"mats": "Sulfur ×20 + Charcoal ×30",  "time": "1s/unit",  "station": "Mixing Table"},
    "sulfur":      {"mats": "Sulfur Ore (Furnace)",        "time": "2.5s/ore", "station": "Furnace"},
    "metal frag":  {"mats": "Metal Ore (Furnace)",         "time": "0.5s/ore", "station": "Furnace"},
    "hqm":         {"mats": "HQM Ore (Furnace)",           "time": "0.5s/ore", "station": "Furnace"},
    "charcoal":    {"mats": "Wood (Furnace)",               "time": "2s/wood",  "station": "Furnace"},
    "lgf":         {"mats": "Animal Fat ×3 + Cloth ×1",   "time": "1s/unit",  "station": "Campfire"},
    "cloth":       {"mats": "Hemp Fiber × varies",         "time": "—",        "station": "Grow Hemp"},
    "rope":        {"mats": "Cloth ×10",                   "time": "5s",       "station": "Inventory"},
    "tarp":        {"mats": "Cloth ×50",                   "time": "30s",      "station": "Inventory"},
    "sewing kit":  {"mats": "Rope ×8 + Cloth ×20",        "time": "15s",      "station": "Inventory"},
    "tech trash":  {"mats": "Recycled from electronics",   "time": "—",        "station": "Recycler"},
}

RES_EMOJIS = {
    "sulfur": "🟡", "wood": "🪵", "metal": "🔩",
    "hqm": "💎", "scrap": "⚙️", "stone": "🪨", "charcoal": "⬛",
}

KITS = [
    ("🔰 Kit Starter",    "AK-47 · Semi Pistol · 500 ammo · Bandage ×5",           "Sem cooldown"),
    ("⚔️ Kit PVP",        "AK-47 · Metal Armor set · 1000 ammo · Med Kit ×3",       "24h cooldown"),
    ("💣 Kit Raider",     "C4 ×4 · Rockets ×8 · Satchels ×6 · Pickaxe",            "48h cooldown"),
    ("🌾 Kit Farmer",     "Jackhammer · Chainsaw · 1k Wood · 1k Stone · 500 Metal", "12h cooldown"),
    ("🏗️ Kit Builder",    "Building Plan · Hammer · 5k Wood · 3k Stone · 1k Metal", "24h cooldown"),
    ("🔍 Kit Scout",      "Bolt Rifle · Scope 8x · 200 HV ammo · Ghillie Suit",     "24h cooldown"),
    ("👑 Kit VIP",        "Full HQM set · M249 · 2k ammo · C4 ×2 · Rockets ×4",    "72h cooldown"),
]


class ResourcesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /calc ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="calc", description="Calcula explosivos para destruir paredes.")
    @app_commands.describe(walls="Número de paredes (1–500)", type="Tipo de parede")
    async def calc(self, interaction: discord.Interaction,
                   walls: int, type: Literal["stone", "metal", "hqm"]):
        if not 1 <= walls <= 500:
            await interaction.response.send_message("❌ Número entre 1 e 500.", ephemeral=True)
            return
        d = CALC_DATA[type]
        labels = {"stone": "🪨 Stone", "metal": "🔩 Metal", "hqm": "💎 HQM (Armored)"}
        embed = rust_embed(
            f"💣 Calc — {labels[type]} × {walls}",
            f"Explosivos para **{walls}** parede(s) de **{labels[type]}**:",
            color=RUST_RED,
        )
        embed.add_field(name="🚀 Foguetes",          value=f"`{d['rockets']*walls:,}`",   inline=True)
        embed.add_field(name="💣 C4",                 value=f"`{d['c4']*walls:,}`",        inline=True)
        embed.add_field(name="🔫 Explo Ammo",         value=f"`{d['explo']*walls:,}`",     inline=True)
        embed.add_field(name="🟡 Sulfur (foguetes)",  value=f"`{d['sulfur_r']*walls:,}`",  inline=True)
        embed.add_field(name="🟡 Sulfur (C4)",        value=f"`{d['sulfur_c4']*walls:,}`", inline=True)
        embed.add_field(name="⛽ Low Grade (foguetes)",value=f"`{d['lgf']*walls:,}`",      inline=True)
        embed.set_footer(text="🦀 Valores aproximados para Rust vanilla | Rust Clan Bot v2.0")
        await interaction.response.send_message(embed=embed)

    # ── /farm ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="farm", description="Registra a farm diária de um recurso.")
    @app_commands.describe(resource="Recurso farmado", amount="Quantidade obtida")
    async def farm(self, interaction: discord.Interaction,
                   resource: Literal["sulfur", "wood", "metal", "hqm", "scrap", "stone", "charcoal"],
                   amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Quantidade deve ser > 0.", ephemeral=True)
            return
        gid = interaction.guild_id
        entry = {
            "resource": resource, "amount": amount,
            "member_id": interaction.user.id,
            "member_name": interaction.user.display_name,
            "ts": datetime.now(timezone.utc),
        }
        data.farm_log.setdefault(gid, []).append(entry)

        # Running total for this resource
        total = sum(e["amount"] for e in data.farm_log[gid] if e["resource"] == resource)

        emoji = RES_EMOJIS.get(resource, "📦")
        embed = rust_embed(
            f"{emoji} Farm Registrada",
            f"{interaction.user.mention} farmou `{amount:,}` de **{resource.title()}**",
            color=RUST_ORANGE,
        )
        embed.add_field(name="📊 Total da sessão", value=f"`{total:,}` de {resource.title()}", inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /base ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="base", description="Registra a localização de uma base no mapa.")
    @app_commands.describe(name="Nome da base", grid="Grid no mapa — ex: D8")
    async def base(self, interaction: discord.Interaction, name: str, grid: str):
        gid = interaction.guild_id
        entry = {
            "name": name, "grid": grid.upper(),
            "added_by": interaction.user.display_name,
            "added_by_id": interaction.user.id,
            "ts": datetime.now(timezone.utc),
        }
        data.base_locations.setdefault(gid, []).append(entry)
        bases = data.base_locations[gid]
        embed = rust_embed("🏠 Base Registrada", f"**{name}** adicionada ao mapa.", color=RUST_ORANGE)
        embed.add_field(name="📍 Grid",          value=f"`{grid.upper()}`",          inline=True)
        embed.add_field(name="👤 Por",           value=interaction.user.mention,    inline=True)
        embed.add_field(name="🗺️ Total de bases", value=str(len(bases)),             inline=True)
        if len(bases) > 1:
            lista = "\n".join(f"• **{b['name']}** — `{b['grid']}`" for b in bases[-5:])
            embed.add_field(name="📋 Últimas bases", value=lista, inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /kit ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="kit", description="Lista os kits disponíveis no servidor.")
    async def kit(self, interaction: discord.Interaction):
        embed = rust_embed("🎒 Kits Disponíveis", color=RUST_COLOR)
        for name, contents, cooldown in KITS:
            embed.add_field(
                name=name,
                value=f"**Conteúdo:** {contents}\n**⏱️ Cooldown:** {cooldown}",
                inline=False,
            )
        embed.set_footer(text="🦀 Digite o nome do kit in-game | Rust Clan Bot v2.0")
        await interaction.response.send_message(embed=embed)

    # ── /bp ───────────────────────────────────────────────────────────────────

    @app_commands.command(name="bp", description="Custo de blueprint e bancada para um item.")
    @app_commands.describe(item="Nome do item — ex: ak47, c4, rocket, mp5")
    async def bp(self, interaction: discord.Interaction, item: str):
        key = item.lower().replace(" ", "").replace("-", "").replace("_", "")
        # Fuzzy match
        match = None
        for k in BP_DATA:
            if key in k.replace("_", "") or k.replace("_", "") in key:
                match = k
                break
        if not match:
            keys = ", ".join(f"`{k}`" for k in list(BP_DATA.keys())[:10])
            await interaction.response.send_message(
                f"❌ Item `{item}` não encontrado. Exemplos: {keys}…", ephemeral=True
            )
            return
        d = BP_DATA[match]
        embed = rust_embed(f"🔬 Blueprint — {match.replace('_', ' ').title()}", color=RUST_ORANGE)
        embed.add_field(name="💰 Custo (Research Table)", value=f"`{d['scrap']} Scrap`",  inline=True)
        embed.add_field(name="🏭 Bancada",                 value=f"`{d['workbench']}`",    inline=True)
        embed.add_field(name="⏱️ Tempo de Craft",          value=f"`{d['time']}`",         inline=True)
        embed.add_field(name="📦 Materiais",                value=d["mats"],                inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /decay ────────────────────────────────────────────────────────────────

    @app_commands.command(name="decay", description="Tempo de decay de estruturas no Rust.")
    @app_commands.describe(structure="Estrutura — ex: stone wall, wood floor, hqm foundation")
    async def decay(self, interaction: discord.Interaction, structure: str):
        key = structure.lower().strip()
        time = DECAY_DATA.get(key)
        if not time:
            close = [k for k in DECAY_DATA if any(w in k for w in key.split())]
            if close:
                lines = "\n".join(f"• `{k}` → **{DECAY_DATA[k]}**" for k in close[:6])
                embed = rust_embed("⏳ Sugestões de Decay", lines, color=RUST_ORANGE)
            else:
                options = "\n".join(f"• `{k}`" for k in list(DECAY_DATA.keys())[:12])
                embed = rust_embed("❌ Estrutura não encontrada",
                                   f"Opções disponíveis:\n{options}", color=RUST_RED)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = rust_embed(
            f"⏳ Decay — {structure.title()}",
            f"A estrutura **{structure.title()}** decai em **{time}** sem upkeep.",
            color=RUST_ORANGE,
        )
        await interaction.response.send_message(embed=embed)

    # ── /upkeep ───────────────────────────────────────────────────────────────

    @app_commands.command(name="upkeep", description="Calcula o custo de upkeep da base por dia.")
    @app_commands.describe(stone="Qtd. blocos de stone", metal="Qtd. blocos de metal", hqm="Qtd. blocos de HQM")
    async def upkeep(self, interaction: discord.Interaction,
                     stone: int = 0, metal: int = 0, hqm: int = 0):
        if stone + metal + hqm == 0:
            await interaction.response.send_message("❌ Informe pelo menos um tipo de bloco.", ephemeral=True)
            return
        # Rust upkeep rates per 24h (approximate):
        # Stone: ~5 stone/hr/block → 120/day; Metal: ~2 metal frag/hr → 48/day; HQM: ~1 HQM/hr → 24/day
        stone_day  = stone * 120
        metal_day  = metal * 48
        hqm_day    = hqm * 24

        embed = rust_embed(
            "🏚️ Custo de Upkeep — 24h",
            f"Base com **{stone}** stone + **{metal}** metal + **{hqm}** HQM:",
            color=RUST_ORANGE,
        )
        if stone:
            embed.add_field(name="🪨 Stone/dia",         value=f"`{stone_day:,}`",  inline=True)
        if metal:
            embed.add_field(name="🔩 Metal Frags/dia",   value=f"`{metal_day:,}`",  inline=True)
        if hqm:
            embed.add_field(name="💎 HQM/dia",           value=f"`{hqm_day:,}`",   inline=True)
        embed.add_field(name="📆 Stone/semana",   value=f"`{stone_day*7:,}`",  inline=True)
        embed.add_field(name="📆 Metal/semana",   value=f"`{metal_day*7:,}`",  inline=True)
        embed.add_field(name="📆 HQM/semana",     value=f"`{hqm_day*7:,}`",   inline=True)
        embed.set_footer(text="🦀 Valores aproximados | Rust Clan Bot v2.0")
        await interaction.response.send_message(embed=embed)

    # ── /crafting ─────────────────────────────────────────────────────────────

    @app_commands.command(name="crafting", description="Receita de craft e estação necessária.")
    @app_commands.describe(item="Item a consultar — ex: gunpowder, lgf, cloth, rope")
    async def crafting(self, interaction: discord.Interaction, item: str):
        key = item.lower().strip().replace("-", " ")
        match = None
        for k in CRAFTING_DATA:
            if key in k or k in key:
                match = k
                break
        if not match:
            options = ", ".join(f"`{k}`" for k in CRAFTING_DATA.keys())
            await interaction.response.send_message(
                f"❌ Item não encontrado. Disponíveis: {options}", ephemeral=True
            )
            return
        d = CRAFTING_DATA[match]
        embed = rust_embed(f"🔧 Crafting — {match.title()}", color=RUST_ORANGE)
        embed.add_field(name="📦 Materiais",  value=d["mats"],    inline=False)
        embed.add_field(name="⏱️ Tempo",      value=d["time"],    inline=True)
        embed.add_field(name="🏭 Estação",    value=d["station"], inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ResourcesCog(bot))
