import asyncio
from datetime import datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands

import data
from helpers import rust_embed, RUST_COLOR, countdown


def build_status_embed(guild: discord.Guild, bot: commands.Bot) -> discord.Embed:
    online = sum(1 for m in guild.members
                 if not m.bot and m.status != discord.Status.offline)
    embed = rust_embed("📊 Status do Servidor — Clan Bot", color=RUST_COLOR)
    embed.add_field(name="🏷️ Servidor",    value=guild.name,                             inline=True)
    embed.add_field(name="👥 Membros",      value=str(guild.member_count),                inline=True)
    embed.add_field(name="🌐 Online",       value=str(online),                            inline=True)
    embed.add_field(name="📡 Latência",     value=f"`{round(bot.latency * 1000)}ms`",     inline=True)
    embed.add_field(name="🤖 Comandos",     value=str(len(bot.tree.get_commands())),      inline=True)
    embed.add_field(name="🔌 Cogs",         value=str(len(bot.cogs)),                     inline=True)

    guild_wipes = data.wipes.get(guild.id, [])
    if guild_wipes:
        wipe_lines = []
        for w in sorted(guild_wipes, key=lambda e: e["dt"])[:3]:
            dt = w["dt"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            wipe_lines.append(f"🌍 **{w['name']}** — ⏳ {countdown(dt)}")
        embed.add_field(name="🗓️ Próximos Wipes", value="\n".join(wipe_lines), inline=False)
    else:
        embed.add_field(name="🗓️ Próximos Wipes", value="*Nenhum registrado*", inline=False)

    now = datetime.now(timezone.utc)
    embed.add_field(name="🕐 Atualizado", value=f"<t:{int(now.timestamp())}:F>", inline=False)
    embed.set_footer(text="🔄 Atualiza a cada 60s | Rust Clan Bot v2.0")
    return embed


class StatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._task = None

    async def cog_load(self):
        self._task = self.bot.loop.create_task(self._status_loop())

    async def cog_unload(self):
        if self._task:
            self._task.cancel()

    async def _status_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_id, (channel_id, message_id) in list(data.status_channels.items()):
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                try:
                    msg = await channel.fetch_message(message_id)
                    await msg.edit(embed=build_status_embed(guild, self.bot))
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    data.status_channels.pop(guild_id, None)
            await asyncio.sleep(60)

    @app_commands.command(name="serverstatus",
                          description="Cria/atualiza embed de status ao vivo em #🤖-status-bot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def serverstatus(self, interaction: discord.Interaction):
        channel = (
            discord.utils.get(interaction.guild.text_channels, name="🤖-status-bot") or
            discord.utils.get(interaction.guild.text_channels, name="status-bot")
        )
        if not channel:
            await interaction.response.send_message(
                "❌ Canal `#🤖-status-bot` não encontrado. Use `/setupserver` primeiro.", ephemeral=True
            )
            return
        embed = build_status_embed(interaction.guild, self.bot)
        msg = await channel.send(embed=embed)
        data.status_channels[interaction.guild_id] = (channel.id, msg.id)
        await interaction.response.send_message(
            f"✅ Status ao vivo ativo em {channel.mention}! Atualiza a cada 60s.", ephemeral=True
        )

    @serverstatus.error
    async def serverstatus_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você precisa de permissão de **Administrador**.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))
