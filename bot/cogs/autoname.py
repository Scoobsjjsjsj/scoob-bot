import asyncio
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_ORANGE, RUST_RED, build_nick, AUTONAME_PREFIX


class AutonameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
                               f"Novos membros receberão o nick: `{AUTONAME_PREFIX}[emoji] nome`",
                               color=RUST_ORANGE)
        await interaction.response.send_message(embed=embed)

    @autoname.error
    async def autoname_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Apelidos**.", ephemeral=True)

    # ── /nameall ──────────────────────────────────────────────────────────────

    @app_commands.command(name="nameall", description=f"Aplica o prefixo 𝗦𝗰𝗼𝗼𝗯 | a TODOS os membros atuais.")
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

    # ── on_member_join (autoname only if already verified/has role) ───────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Autoname is applied post-verification in verification.py
        pass

    # ── on_member_update (role change → update nick) ──────────────────────────

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return
        if after.guild.id not in data.autoname_guilds:
            return
        # Only update if they have at least Recruta
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
