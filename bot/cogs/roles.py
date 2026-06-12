import asyncio
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import (rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE,
                     CLAN_ROLE_DEFS, CLAN_ROLE_NAMES, CLAN_ROLE_EMOJIS,
                     OFICIAL_PLUS, has_oficial_plus, build_nick,
                     to_bold_unicode, resolve_theme, get_server_emoji)

ROLE_LITERAL = Literal[
    "👑 Lider", "⚔️ Co-Lider", "🛡️ Oficial", "💣 Raider", "🎯 PVP",
    "🌿 Roamer", "🏗️ Builder", "⚡ Eletricista", "🌾 Farmer",
    "🤖 BotFarmer", "🔍 Scout", "🎮 Membro", "🆕 Recruta"
]

SQUAD_ROLES = ["Raider", "Farmer", "Builder", "Scout", "Lider", "Roamer", "PVP", "Eletricista", "BotFarmer"]


class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    SPECIAL_ROLES = [
        ("Raider",      "\U0001f4a3", "Raider"),
        ("Co-Lider",    "\U0001f4ab", "Co-Lider"),
        ("Roamer",      "\U0001f33f", "Roamer"),
        ("Eletricista", "\u26a1", "Eletricista"),
        ("Builder",     "\U0001f3d7\ufe0f", "Builder"),
        ("Farmer",      "\U0001f33e", "Farmer"),
        ("BotFarmer",   "\U0001f916", "BotFarmer"),
        ("PVP",         "\U0001f3af", "PVP"),
        ("Scout",       "\U0001f50d", "Scout"),
    ]

    MAIN_ROLES = [
        ("Lider",   "\U0001f451", "Lider"),
        ("Oficial", "\U0001f6e1\ufe0f", "Oficial"),
        ("Membro",  "\U0001f3ae", "Membro"),
        ("Recruta", "\U0001f195", "Recruta"),
    ]

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return

        especial = None
        for keyword, emoji, label in self.SPECIAL_ROLES:
            for role in after.roles:
                if keyword.lower() in role.name.lower():
                    especial = (emoji, label)
                    break
            if especial:
                break

        principal = None
        for keyword, emoji, label in self.MAIN_ROLES:
            for role in after.roles:
                if keyword.lower() in role.name.lower():
                    principal = (emoji, label)
                    break
            if principal:
                break

        if not principal:
            return

        current = after.display_name
        original = current
        if original.startswith("Scoob <> "):
            original = original[9:]
        if "|" in original:
            original = original.split("|")[0].strip()
        original = original.strip()

        if especial:
            emoji_e, label_e = especial
            emoji_p, label_p = principal
            novo_nick = f"Scoob <> {original} | {emoji_e}{label_e} | {emoji_p}{label_p}"
        else:
            emoji_p, label_p = principal
            novo_nick = f"Scoob <> {original} | {emoji_p}{label_p}"

        novo_nick = novo_nick[:32]
        if after.display_name != novo_nick:
            try:
                await after.edit(nick=novo_nick)
            except:
                pass

    # ── /giverole ─────────────────────────────────────────────────────────────

    @app_commands.command(name="giverole", description="Dá um cargo do clan a um membro (requer Oficial+).")
    @app_commands.describe(user="Membro alvo", role="Cargo a atribuir")
    async def giverole(self, interaction: discord.Interaction, user: discord.Member, role: ROLE_LITERAL):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return

        discord_role = discord.utils.get(interaction.guild.roles, name=role)
        if not discord_role:
            await interaction.response.send_message(
                f"❌ Cargo **{role}** não existe. Use `/setuproles` primeiro.", ephemeral=True
            )
            return
        try:
            await user.add_roles(discord_role, reason=f"giverole por {interaction.user}")
            if interaction.guild_id in data.autoname_guilds:
                try:
                    await user.edit(nick=build_nick(user))
                except discord.Forbidden:
                    pass
            embed = rust_embed("✅ Cargo Atribuído",
                               f"{user.mention} recebeu **{role}**", color=RUST_ORANGE)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para atribuir este c
