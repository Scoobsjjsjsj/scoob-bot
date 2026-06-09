import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime


class DivulgarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="divulgar", description="Gera uma mensagem bonita para divulgar o servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def divulgar(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            invite = await interaction.channel.create_invite(
                max_age=0, max_uses=0, unique=False, reason="Divulgação do clã"
            )
            link = invite.url
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar convite neste canal.", ephemeral=True)
            return

        guild = interaction.guild
        member_count = guild.member_count

        embed = discord.Embed(
            title="🐕 𝗦𝗰𝗼𝗼𝗯 𝗢𝗧 — 𝗖𝗹ã 𝗱𝗲 𝗥𝘂𝘀𝘁 🇧🇷",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🎮 **Clã brasileiro de RUST**\n"
                "💣 Focado em **Zerg** e **PVP** agressivo\n"
                "🏆 Servidores **Atlas US/EU 10x**\n"
                "🔥 Wipes organizados toda semana\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFF4500
        )

        embed.add_field(
            name="⚔️ O que oferecemos",
            value=(
                "💣 Raids organizadas diariamente\n"
                "🌾 Farm em equipe\n"
                "🏗️ Bases grandes e seguras\n"
                "🎯 PVP competitivo\n"
                "👑 Liderança ativa 24h"
            ),
            inline=True
        )

        embed.add_field(
            name="📊 Servidor",
            value=(
                f"👥 **{member_count}** membros\n"
                "🌍 Brasil 🇧🇷\n"
                "🎮 RUST\n"
                "🔊 Discord sempre ativo\n"
                "🗓️ Wipes semanais"
            ),
            inline=True
        )

        embed.add_field(
            name="🔗 Entre agora!",
            value=f"**[👉 Clique aqui para entrar no clã!]({link})**\n`{link}`",
            inline=False
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(text="🦀 Scoob OT • Rust Clan Brasil • Venha fazer parte!")
        embed.timestamp = datetime.utcnow()

        await interaction.channel.send("@everyone", embed=embed)
        await interaction.followup.send("✅ Mensagem de divulgação enviada!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DivulgarCog(bot))
