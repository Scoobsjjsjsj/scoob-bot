import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, RUST_RED, RUST_ORANGE, countdown


def parse_dt(date_str: str, time_str: str) -> datetime | None:
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def wipe_embed(entry: dict, guild: discord.Guild) -> discord.Embed:
    dt: datetime = entry["dt"]
    embed = rust_embed(
        f"🗓️ WIPE — {entry['name']}",
        f"**O wipe está chegando! Prepara tudo!** 💣",
        color=RUST_RED,
    )
    embed.add_field(name="🌍 Servidor",   value=f"`{entry['name']}`",                           inline=True)
    embed.add_field(name="📅 Data",       value=f"`{dt.strftime('%d/%m/%Y')}`",                  inline=True)
    embed.add_field(name="🕐 Hora (UTC)", value=f"`{dt.strftime('%H:%M')} UTC`",                 inline=True)
    embed.add_field(name="🔌 Connect IP", value=f"```{entry['ip']}```",                          inline=False)
    embed.add_field(name="⏰ Countdown",  value=f"**{countdown(dt)}**",                          inline=False)
    embed.add_field(name="📌 Unix",       value=f"<t:{int(dt.timestamp())}:F>",                  inline=False)
    embed.set_image(url="https://i.imgur.com/ZqE6dR6.png")
    embed.set_footer(text=f"🦀 Rust Clan Bot v2.0 • {guild.name}")
    return embed


class WipeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._reminder_task = None

    async def cog_load(self):
        self._reminder_task = self.bot.loop.create_task(self._wipe_reminder_loop())

    async def cog_unload(self):
        if self._reminder_task:
            self._reminder_task.cancel()

    async def _wipe_reminder_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now(timezone.utc)
            for guild_id, guild_wipes in list(data.wipes.items()):
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                for entry in guild_wipes:
                    dt: datetime = entry["dt"]
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    diff = (dt - now).total_seconds()

                    if 3540 <= diff <= 3660 and not entry.get("reminded_1h"):
                        entry["reminded_1h"] = True
                        await self._send_reminder(guild, entry, "1 hora")

                    if 540 <= diff <= 660 and not entry.get("reminded_10m"):
                        entry["reminded_10m"] = True
                        await self._send_reminder(guild, entry, "10 minutos")

            await asyncio.sleep(60)

    async def _send_reminder(self, guild: discord.Guild, entry: dict, time_label: str):
        channel_id = entry.get("channel_id")
        channel = guild.get_channel(channel_id) if channel_id else None
        if not channel:
            channel = discord.utils.get(guild.text_channels, name="📢-anuncios") or \
                      discord.utils.get(guild.text_channels, name="anuncios") or \
                      guild.text_channels[0] if guild.text_channels else None
        if not channel:
            return
        embed = rust_embed(
            f"⏰ LEMBRETE DE WIPE — {time_label}!",
            f"@everyone — O wipe do **{entry['name']}** começa em **{time_label}**!\n"
            f"🔌 `{entry['ip']}`",
            color=RUST_RED,
        )
        embed.add_field(name="⏳ Countdown", value=countdown(entry["dt"]), inline=False)
        try:
            await channel.send(
                "@everyone",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=True),
            )
        except discord.Forbidden:
            pass

    # ── /wipe ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="wipe", description="Registra um wipe e anuncia com @everyone.")
    @app_commands.describe(
        server_name="Nome do servidor — ex: Brasa 2x",
        date="Data DD/MM/YYYY — ex: 15/06/2025",
        time="Hora HH:MM UTC — ex: 20:00",
        connect_ip="IP de conexão — ex: connect 123.45.6.78:28015",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def wipe(self, interaction: discord.Interaction,
                   server_name: str, date: str, time: str, connect_ip: str):
        dt = parse_dt(date, time)
        if not dt:
            await interaction.response.send_message(
                "❌ Formato inválido. Use `DD/MM/YYYY` e `HH:MM`. Ex: `15/06/2025` `20:00`", ephemeral=True
            )
            return

        entry = {
            "name": server_name, "date_str": date, "time_str": time,
            "ip": connect_ip, "dt": dt,
            "channel_id": interaction.channel_id,
            "msg_id": None, "reminded_1h": False, "reminded_10m": False,
        }
        data.wipes.setdefault(interaction.guild_id, []).append(entry)

        embed = wipe_embed(entry, interaction.guild)
        await interaction.response.send_message(
            "@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )
        msg = await interaction.original_response()
        entry["msg_id"] = msg.id

    @wipe.error
    async def wipe_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)

    # ── /wipes ────────────────────────────────────────────────────────────────

    @app_commands.command(name="wipes", description="Lista todos os wipes registrados com countdown.")
    async def wipes_cmd(self, interaction: discord.Interaction):
        guild_wipes = data.wipes.get(interaction.guild_id, [])
        embed = rust_embed("🗓️ Wipes Registrados", color=RUST_COLOR)
        if not guild_wipes:
            embed.description = "*Nenhum wipe registrado. Use `/wipe` para adicionar.*"
        else:
            for entry in sorted(guild_wipes, key=lambda e: e["dt"]):
                dt = entry["dt"]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                embed.add_field(
                    name=f"🌍 {entry['name']}",
                    value=f"📅 `{dt.strftime('%d/%m/%Y %H:%M')} UTC`\n"
                          f"🔌 `{entry['ip']}`\n"
                          f"⏳ Em **{countdown(dt)}**",
                    inline=False,
                )
        await interaction.response.send_message(embed=embed)

    # ── /delwipe ──────────────────────────────────────────────────────────────

    @app_commands.command(name="delwipe", description="Remove um wipe registrado.")
    @app_commands.describe(server_name="Nome do servidor a remover")
    @app_commands.checks.has_permissions(administrator=True)
    async def delwipe(self, interaction: discord.Interaction, server_name: str):
        guild_wipes = data.wipes.get(interaction.guild_id, [])
        before = len(guild_wipes)
        data.wipes[interaction.guild_id] = [
            w for w in guild_wipes if w["name"].lower() != server_name.lower()
        ]
        removed = before - len(data.wipes[interaction.guild_id])
        if removed:
            embed = rust_embed("🗑️ Wipe Removido", f"Wipe **{server_name}** removido.", color=RUST_ORANGE)
        else:
            embed = rust_embed("❌ Não Encontrado", f"Nenhum wipe com o nome **{server_name}**.", color=RUST_RED)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @delwipe.error
    async def delwipe_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(WipeCog(bot))
