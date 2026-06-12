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

    # ── /syncnicks ────────────────────────────────────────────────────────────

    @app_commands.command(name="syncnicks", description="Atualiza o nick de todos os membros com o formato de cargos.")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def syncnicks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        atualizados = 0
        sem_cargo = 0
        erros = 0

        for member in interaction.guild.members:
            if member.bot:
                continue

            especial = None
            for keyword, emoji, label in self.SPECIAL_ROLES:
                for role in member.roles:
                    if keyword.lower() in role.name.lower():
                        especial = (emoji, label)
                        break
                if especial:
                    break

            principal = None
            for keyword, emoji, label in self.MAIN_ROLES:
                for role in member.roles:
                    if keyword.lower() in role.name.lower():
                        principal = (emoji, label)
                        break
                if principal:
                    break

            if not principal:
                sem_cargo += 1
                continue

            current = member.display_name
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

            if member.display_name != novo_nick:
                try:
                    await member.edit(nick=novo_nick)
                    atualizados += 1
                    await asyncio.sleep(0.5)
                except discord.Forbidden:
                    erros += 1
                except Exception:
                    erros += 1

        desc = f"✅ **{atualizados}** nicks atualizados\n"
        desc += f"⚪ **{sem_cargo}** sem cargo definido\n"
        if erros:
            desc += f"❌ **{erros}** erros (permissão)"

        embed = rust_embed("🔄 Sincronização de Nicks", desc, color=RUST_ORANGE)
        await interaction.followup.send(embed=embed)

    @syncnicks.error
    async def syncnicks_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Precisas de permissão **Gerenciar Apelidos**.", ephemeral=True)

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
