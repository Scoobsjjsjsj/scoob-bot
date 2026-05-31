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
            # Update nickname
            if interaction.guild_id in data.autoname_guilds:
                try:
                    await user.edit(nick=build_nick(user))
                except discord.Forbidden:
                    pass
            embed = rust_embed("✅ Cargo Atribuído",
                               f"{user.mention} recebeu **{role}**", color=RUST_ORANGE)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para atribuir este cargo.", ephemeral=True)

    # ── /removerole ───────────────────────────────────────────────────────────

    @app_commands.command(name="removerole", description="Remove um cargo do clan de um membro (requer Oficial+).")
    @app_commands.describe(user="Membro alvo", role="Cargo a remover")
    async def removerole(self, interaction: discord.Interaction, user: discord.Member, role: ROLE_LITERAL):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return

        discord_role = discord.utils.get(interaction.guild.roles, name=role)
        if not discord_role:
            await interaction.response.send_message(f"❌ Cargo **{role}** não existe.", ephemeral=True)
            return
        try:
            await user.remove_roles(discord_role, reason=f"removerole por {interaction.user}")
            if interaction.guild_id in data.autoname_guilds:
                try:
                    await user.edit(nick=build_nick(user))
                except discord.Forbidden:
                    pass
            embed = rust_embed("✅ Cargo Removido",
                               f"{user.mention} perdeu **{role}**", color=RUST_RED)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para remover este cargo.", ephemeral=True)

    # ── /roster ───────────────────────────────────────────────────────────────

    @app_commands.command(name="roster", description="Lista todos os membros agrupados por cargo do clan.")
    async def roster(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = rust_embed("📋 Roster do Clan", color=RUST_COLOR)
        total = 0
        for name, _, _, _, unicode_emoji in CLAN_ROLE_DEFS:
            discord_role = discord.utils.get(interaction.guild.roles, name=name)
            if not discord_role or not discord_role.members:
                continue
            display_emoji = get_server_emoji(interaction.guild, name, unicode_emoji)
            members_str = "\n".join(f"• {m.display_name}" for m in discord_role.members[:15])
            if len(discord_role.members) > 15:
                members_str += f"\n*+{len(discord_role.members) - 15} mais...*"
            embed.add_field(
                name=f"{display_emoji} {name} ({len(discord_role.members)})",
                value=members_str,
                inline=True,
            )
            total += len(discord_role.members)
        if not embed.fields:
            embed.description = "*Nenhum cargo de clan encontrado. Use `/setuproles` primeiro.*"
        embed.set_footer(text=f"🦀 Total: {total} membros com cargos | Rust Clan Bot v2.0")
        await interaction.followup.send(embed=embed)

    # ── /roles (themed role creator) ──────────────────────────────────────────

    @app_commands.command(name="roles", description="Cria um cargo com bold unicode, emoji temático e cor temática.")
    @app_commands.describe(theme="Tema do cargo — ex: fire, dragon, scooby-doo, rust…")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roles_cmd(self, interaction: discord.Interaction, theme: str):
        emoji, color = resolve_theme(theme)
        bold_name = to_bold_unicode(theme.replace("-", " ").title())
        role_name = f"{emoji} {bold_name}"

        existing = discord.utils.get(interaction.guild.roles, name=role_name)
        if existing:
            await interaction.response.send_message(
                f"Cargo **{role_name}** já existe: {existing.mention}", ephemeral=True
            )
            return
        try:
            role = await interaction.guild.create_role(
                name=role_name, color=color, reason=f"/roles por {interaction.user}"
            )
            embed = rust_embed("✅ Cargo Criado", f"Cargo {role.mention} criado com sucesso!", color=RUST_ORANGE)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para criar cargos.", ephemeral=True)

    @roles_cmd.error
    async def roles_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Cargos**.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RolesCog(bot))
