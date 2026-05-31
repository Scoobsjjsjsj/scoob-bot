import asyncio
from datetime import datetime, timezone, timedelta
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_RED, RUST_ORANGE, has_oficial_plus

TIME_UNITS = {"m": 60, "h": 3600, "d": 86400}

def parse_duration(s: str) -> int | None:
    """Parse '10m', '2h', '1d' -> seconds."""
    try:
        unit = s[-1].lower()
        val  = int(s[:-1])
        return val * TIME_UNITS.get(unit, 0)
    except (ValueError, IndexError):
        return None


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /warn ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="warn", description="Avisa um membro. Auto-kick ao 3º aviso.")
    @app_commands.describe(user="Membro a avisar", reason="Motivo do aviso")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
            return

        gid = interaction.guild_id
        data.warnings.setdefault(gid, {}).setdefault(user.id, []).append({
            "reason": reason,
            "ts": datetime.now(timezone.utc),
            "by_name": str(interaction.user),
        })
        count = len(data.warnings[gid][user.id])

        embed = rust_embed(
            f"⚠️ Aviso #{count} — {user.display_name}",
            f"**Motivo:** {reason}",
            color=RUST_ORANGE,
        )
        embed.add_field(name="👤 Avisado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="⚠️ Total avisos", value=str(count), inline=True)

        await interaction.response.send_message(embed=embed)

        try:
            dm = rust_embed(
                f"⚠️ Você recebeu um aviso em {interaction.guild.name}",
                f"**Motivo:** {reason}\n**Avisos totais:** {count}/3",
                color=RUST_ORANGE,
            )
            await user.send(embed=dm)
        except discord.Forbidden:
            pass

        # Log to #anuncios
        log_ch = (discord.utils.get(interaction.guild.text_channels, name="📢-anuncios") or
                  discord.utils.get(interaction.guild.text_channels, name="anuncios"))
        if log_ch:
            try:
                await log_ch.send(embed=embed)
            except discord.Forbidden:
                pass

        if count >= 3:
            try:
                kick_dm = rust_embed("🚫 Você foi kickado", f"3 avisos acumulados em **{interaction.guild.name}**.", color=RUST_RED)
                await user.send(embed=kick_dm)
            except discord.Forbidden:
                pass
            try:
                await user.kick(reason="3 avisos acumulados")
                await interaction.channel.send(embed=rust_embed("🚫 Kick Automático",
                    f"{user.mention} foi kickado por acumular **3 avisos**.", color=RUST_RED))
            except discord.Forbidden:
                pass

    @warn.error
    async def warn_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Sem permissão para avisar membros.", ephemeral=True)

    # ── /warnings ─────────────────────────────────────────────────────────────

    @app_commands.command(name="warnings", description="Mostra todos os avisos de um membro.")
    @app_commands.describe(user="Membro a consultar")
    async def warnings_cmd(self, interaction: discord.Interaction, user: discord.Member):
        warns = data.warnings.get(interaction.guild_id, {}).get(user.id, [])
        embed = rust_embed(f"⚠️ Avisos — {user.display_name}",
                           f"Total: **{len(warns)}** aviso(s)", color=RUST_ORANGE)
        for i, w in enumerate(warns[-10:], 1):
            ts = w["ts"].strftime("%d/%m/%Y %H:%M") if isinstance(w["ts"], datetime) else str(w["ts"])
            embed.add_field(name=f"#{i} — {ts}", value=f"**Motivo:** {w['reason']}\n**Por:** {w['by_name']}", inline=False)
        if not warns:
            embed.description = "✅ Nenhum aviso registrado."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /clearwarns ───────────────────────────────────────────────────────────

    @app_commands.command(name="clearwarns", description="Limpa todos os avisos de um membro (Oficial+).")
    @app_commands.describe(user="Membro a limpar avisos")
    async def clearwarns(self, interaction: discord.Interaction, user: discord.Member):
        if not has_oficial_plus(interaction.user) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser **Oficial ou superior**.", ephemeral=True)
            return
        data.warnings.setdefault(interaction.guild_id, {}).pop(user.id, None)
        await interaction.response.send_message(
            embed=rust_embed("✅ Avisos Limpos", f"Todos os avisos de {user.mention} foram removidos.", color=RUST_ORANGE)
        )

    # ── /mute ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="mute", description="Muta um membro por um período. Ex: 10m, 2h, 1d")
    @app_commands.describe(user="Membro a mutar", duration="Duração: 10m, 2h, 1d", reason="Motivo")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member,
                   duration: str, reason: str = "Sem motivo especificado"):
        secs = parse_duration(duration)
        if not secs:
            await interaction.response.send_message("❌ Duração inválida. Use `10m`, `2h` ou `1d`.", ephemeral=True)
            return
        until = discord.utils.utcnow() + timedelta(seconds=secs)
        try:
            await user.timeout(until, reason=reason)
            embed = rust_embed("🔇 Membro Mutado", f"{user.mention} foi mutado por `{duration}`.\n**Motivo:** {reason}", color=RUST_RED)
            await interaction.response.send_message(embed=embed)
            try:
                await user.send(embed=rust_embed("🔇 Você foi mutado",
                    f"**Duração:** {duration}\n**Motivo:** {reason}\n**Servidor:** {interaction.guild.name}", color=RUST_RED))
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para mutar este membro.", ephemeral=True)

    @mute.error
    async def mute_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Moderar Membros**.", ephemeral=True)

    # ── /unmute ───────────────────────────────────────────────────────────────

    @app_commands.command(name="unmute", description="Remove o mute de um membro.")
    @app_commands.describe(user="Membro a desmutar")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        try:
            await user.timeout(None)
            await interaction.response.send_message(
                embed=rust_embed("🔊 Membro Desmutado", f"{user.mention} pode falar novamente.", color=RUST_ORANGE)
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

    @unmute.error
    async def unmute_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Moderar Membros**.", ephemeral=True)

    # ── /kick ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="kick", description="Kicka um membro do servidor.")
    @app_commands.describe(user="Membro a kickar", reason="Motivo")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member,
                   reason: str = "Sem motivo especificado"):
        try:
            await user.send(embed=rust_embed("🚫 Você foi kickado",
                f"**Servidor:** {interaction.guild.name}\n**Motivo:** {reason}", color=RUST_RED))
        except discord.Forbidden:
            pass
        try:
            await user.kick(reason=reason)
            await interaction.response.send_message(
                embed=rust_embed("🚫 Membro Kickado", f"{user.mention} foi kickado.\n**Motivo:** {reason}", color=RUST_RED)
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para kickar.", ephemeral=True)

    @kick.error
    async def kick_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Expulsar Membros**.", ephemeral=True)

    # ── /ban ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="ban", description="Bane um membro permanentemente.")
    @app_commands.describe(user="Membro a banir", reason="Motivo")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member,
                  reason: str = "Sem motivo especificado"):
        try:
            await user.send(embed=rust_embed("🔨 Você foi banido",
                f"**Servidor:** {interaction.guild.name}\n**Motivo:** {reason}", color=RUST_RED))
        except discord.Forbidden:
            pass
        try:
            await user.ban(reason=reason, delete_message_days=0)
            await interaction.response.send_message(
                embed=rust_embed("🔨 Membro Banido", f"{user.mention} foi banido.\n**Motivo:** {reason}", color=RUST_RED)
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para banir.", ephemeral=True)

    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Banir Membros**.", ephemeral=True)

    # ── /slowmode ─────────────────────────────────────────────────────────────

    @app_commands.command(name="slowmode", description="Define o slowmode do canal (0 para desativar).")
    @app_commands.describe(seconds="Segundos (0–21600)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if not 0 <= seconds <= 21600:
            await interaction.response.send_message("❌ Valor entre 0 e 21600 segundos.", ephemeral=True)
            return
        await interaction.channel.edit(slowmode_delay=seconds)
        msg = f"⏱️ Slowmode definido para **{seconds}s**." if seconds else "⏱️ Slowmode **desativado**."
        await interaction.response.send_message(embed=rust_embed("⏱️ Slowmode", msg, color=RUST_ORANGE))

    @slowmode.error
    async def slowmode_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Canais**.", ephemeral=True)

    # ── /lock / /unlock ───────────────────────────────────────────────────────

    @app_commands.command(name="lock", description="Bloqueia o canal para membros comuns.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(
            embed=rust_embed("🔒 Canal Bloqueado", f"{interaction.channel.mention} foi bloqueado.", color=RUST_RED)
        )

    @lock.error
    async def lock_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Canais**.", ephemeral=True)

    @app_commands.command(name="unlock", description="Desbloqueia o canal.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(
            embed=rust_embed("🔓 Canal Desbloqueado", f"{interaction.channel.mention} foi desbloqueado.", color=RUST_ORANGE)
        )

    @unlock.error
    async def unlock_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão **Gerenciar Canais**.", ephemeral=True)

    # ── !limpar ───────────────────────────────────────────────────────────────

    @commands.command(name="limpar")
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx: commands.Context, n: int):
        if not 1 <= n <= 500:
            await ctx.send("Por favor, use um número entre 1 e 500.", delete_after=5)
            return
        deleted = 0
        async for msg in ctx.channel.history(limit=n + 1):
            try:
                await msg.delete()
                deleted += 1
                await asyncio.sleep(0.35)
            except (discord.Forbidden, discord.NotFound):
                pass
        confirm = await ctx.send(f"🗑️ **{deleted}** mensagens deletadas.")
        await asyncio.sleep(4)
        try:
            await confirm.delete()
        except discord.NotFound:
            pass

    @limpar.error
    async def limpar_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você precisa de permissão **Gerenciar Mensagens**.", delete_after=5)
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send("Uso: `!limpar [N]` — ex: `!limpar 20`", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
