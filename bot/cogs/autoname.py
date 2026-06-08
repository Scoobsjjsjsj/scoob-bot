import asyncio
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_ORANGE, RUST_RED, build_nick, AUTONAME_PREFIX, AUTONAME_EMOJI


class AutonameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # autorole: guild_id -> role_id
        self.autorole_guilds: dict[int, int] = {}

    # ── /autoname ─────────────────────────────────────────────────────────────

    @app_commands.command(name="autoname", description="Ativa/desativa o prefixo automático para novos membros.")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def autoname(self, interaction: discord.Interaction):
        gid = interaction.guild_id
        if gid in data.autoname_guilds:
            data.autoname_guilds.discard(gid)
            embed = rust_embed("🏷️ Autoname Desativado",
                               "Novos membros **não** receberão mais o prefixo automático.", color=RUST_RED)
        else:
            data.autoname_guilds.add(gid)
            embed = rust_embed("🏷️ Autoname Ativado",
                               f"Novos membros receberão o nick: `{AUTONAME_PREFIX}{AUTONAME_EMOJI} nome`",
                               color=RUST_ORANGE)
        await interaction.response.send_message(embed=embed)

    @autoname.error
    async def autoname_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Apelidos**.", ephemeral=True)

    # ── /nameall ──────────────────────────────────────────────────────────────

    @app_commands.command(name="nameall", description="Aplica o prefixo 𝗦𝗰𝗼𝗼𝗯 | 🐕 a TODOS os membros atuais.")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nameall(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success, skipped, failed = 0, 0, 0
        for member in interaction.guild.members:
            if member.bot:
                skipped += 1
                continue
            nick = build_nick(member)
            if member.nick == nick:
                skipped += 1
                continue
            try:
                await member.edit(nick=nick)
                success += 1
            except discord.Forbidden:
                failed += 1
            await asyncio.sleep(0.5)

        embed = rust_embed(
            "✅ Nameall Concluído",
            f"✅ **{success}** renomeados\n"
            f"⏭️ **{skipped}** ignorados (bots / já correto)\n"
            f"❌ **{failed}** falharam (cargo maior ou dono)",
            color=RUST_ORANGE,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @nameall.error
    async def nameall_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Apelidos**.", ephemeral=True)

    # ── /autorole ─────────────────────────────────────────────────────────────

    @app_commands.command(name="autorole", description="Define o cargo que novos membros recebem automaticamente ao entrar.")
    @app_commands.describe(cargo="Cargo a ser dado automaticamente para novos membros")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, cargo: discord.Role):
        gid = interaction.guild_id
        if cargo == interaction.guild.default_role:
            await interaction.response.send_message("❌ Não é possível usar o cargo @everyone.", ephemeral=True)
            return
        self.autorole_guilds[gid] = cargo.id
        embed = rust_embed(
            "✅ AutoRole Configurado",
            f"Novos membros receberão automaticamente o cargo {cargo.mention}!",
            color=RUST_ORANGE
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="autoroledisable", description="Desativa o cargo automático para novos membros.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autoroledisable(self, interaction: discord.Interaction):
        gid = interaction.guild_id
        if gid in self.autorole_guilds:
            self.autorole_guilds.pop(gid)
            embed = rust_embed("❌ AutoRole Desativado", "Novos membros não receberão mais cargo automático.", color=RUST_RED)
        else:
            embed = rust_embed("⚠️ AutoRole", "Nenhum cargo automático estava configurado.", color=RUST_RED)
        await interaction.response.send_message(embed=embed)

    # ── on_member_join ────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        gid = member.guild.id

        # AutoRole
        if gid in self.autorole_guilds:
            role_id = self.autorole_guilds[gid]
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="AutoRole automático")
                except discord.Forbidden:
                    pass

        # AutoName
        if gid in data.autoname_guilds:
            nick = build_nick(member)
            try:
                await member.edit(nick=nick)
            except discord.Forbidden:
                pass

    # ── on_member_update ──────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return
        if after.guild.id not in data.autoname_guilds:
            return
        has_any_clan_role = any(
            r.name in {"👑 Lider", "⚔️ Co-Lider", "🛡️ Oficial", "💣 Raider",
                       "🎯 PVP", "🌿 Roamer", "🏗️ Builder", "⚡ Eletricista",
                       "🌾 Farmer", "🤖 BotFarmer", "🔍 Scout", "🎮 Membro", "🆕 Recruta"}
            for r in after.roles
        )
        if not has_any_clan_role:
            return
        try:
            new_nick = build_nick(after)
            if after.nick != new_nick:
                await after.edit(nick=new_nick)
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AutonameCog(bot))
